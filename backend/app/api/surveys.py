import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.session import get_db
from app.models.models import Survey, Parcel, CadastralFeature, BoundaryChange, SurveyStatus, ParcelStatus
from app.schemas.schemas import SurveyCreate, SurveyResponse, SurveyUpdate, SurveyStatisticsResponse
from app.auth.security import get_current_user, require_roles
from app.services.storage import storage_service
from app.services.pipeline import run_survey_pipeline
from app.services.demo_data import seed_demo_dataset

router = APIRouter(prefix="/surveys", tags=["Surveys"])

@router.get("", response_model=List[SurveyResponse])
def get_surveys(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    surveys = db.query(Survey).order_by(Survey.id.desc()).offset(skip).limit(limit).all()
    res = []
    for s in surveys:
        p_count = db.query(Parcel).filter(Parcel.survey_id == s.id).count()
        v_count = db.query(Parcel).filter(Parcel.survey_id == s.id, Parcel.status == "verified").count()
        d_count = db.query(BoundaryChange).filter(BoundaryChange.survey_id == s.id).count()
        
        s_dict = {
            "id": s.id,
            "name": s.name,
            "village": s.village,
            "mandal": s.mandal,
            "district": s.district,
            "state": s.state,
            "survey_date": s.survey_date,
            "survey_officer": s.survey_officer,
            "description": s.description,
            "status": s.status,
            "processing_progress": s.processing_progress or 0,
            "current_step": s.current_step or "Not started",
            "orthomosaic_filename": s.orthomosaic_filename,
            "cadastral_filename": s.cadastral_filename,
            "created_at": s.created_at,
            "updated_at": s.updated_at,
            "parcel_count": p_count,
            "verified_count": v_count,
            "discrepancy_count": d_count
        }
        res.append(s_dict)
    return res

@router.post("", response_model=SurveyResponse)
def create_survey(
    survey_in: SurveyCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "survey_officer"]))
):
    new_survey = Survey(
        name=survey_in.name,
        village=survey_in.village,
        mandal=survey_in.mandal,
        district=survey_in.district,
        state=survey_in.state,
        survey_date=survey_in.survey_date,
        survey_officer=survey_in.survey_officer,
        description=survey_in.description,
        status=SurveyStatus.DRAFT.value,
        processing_progress=0,
        current_step="Created, waiting for imagery upload",
        created_by=current_user.id
    )
    db.add(new_survey)
    db.commit()
    db.refresh(new_survey)
    return new_survey

@router.get("/{survey_id}", response_model=SurveyResponse)
def get_survey(
    survey_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    s = db.query(Survey).filter(Survey.id == survey_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Survey not found")
    
    p_count = db.query(Parcel).filter(Parcel.survey_id == s.id).count()
    v_count = db.query(Parcel).filter(Parcel.survey_id == s.id, Parcel.status == "verified").count()
    d_count = db.query(BoundaryChange).filter(BoundaryChange.survey_id == s.id).count()

    return {
        "id": s.id,
        "name": s.name,
        "village": s.village,
        "mandal": s.mandal,
        "district": s.district,
        "state": s.state,
        "survey_date": s.survey_date,
        "survey_officer": s.survey_officer,
        "description": s.description,
        "status": s.status,
        "processing_progress": s.processing_progress or 0,
        "current_step": s.current_step or "Not started",
        "orthomosaic_filename": s.orthomosaic_filename,
        "cadastral_filename": s.cadastral_filename,
        "created_at": s.created_at,
        "updated_at": s.updated_at,
        "parcel_count": p_count,
        "verified_count": v_count,
        "discrepancy_count": d_count
    }

@router.post("/{survey_id}/upload")
def upload_survey_files(
    survey_id: int,
    orthomosaic: Optional[UploadFile] = File(None),
    cadastral: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "survey_officer"]))
):
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")

    if orthomosaic:
        saved_path = storage_service.save_upload_file(survey.id, orthomosaic.file, orthomosaic.filename, "input")
        survey.orthomosaic_path = str(saved_path)
        survey.orthomosaic_filename = orthomosaic.filename

    if cadastral:
        saved_cad = storage_service.save_upload_file(survey.id, cadastral.file, cadastral.filename, "input")
        survey.cadastral_path = str(saved_cad)
        survey.cadastral_filename = cadastral.filename

    survey.status = SurveyStatus.UPLOADED.value
    survey.current_step = "Files uploaded, ready for AI pipeline processing"
    db.commit()

    return {
        "message": "Survey files uploaded successfully",
        "orthomosaic": survey.orthomosaic_filename,
        "cadastral": survey.cadastral_filename,
        "status": survey.status
    }

@router.post("/{survey_id}/process")
def process_survey(
    survey_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "survey_officer"]))
):
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")

    # Idempotency guard: If survey is already processing, do not start another background task
    if survey.status == SurveyStatus.PROCESSING.value:
        return {
            "message": "Survey AI pipeline is already actively running",
            "survey_id": survey.id,
            "status": survey.status
        }

    # If no orthomosaic uploaded yet, provide synthetic demo image
    if not survey.orthomosaic_path or not os.path.exists(survey.orthomosaic_path):
        from app.services.demo_data import generate_synthetic_orthomosaic
        ortho_dir = storage_service.get_survey_dir(survey.id) / "processed"
        ortho_path = ortho_dir / f"orthomosaic_srv_{survey.id}.png"
        generate_synthetic_orthomosaic(ortho_path)
        survey.orthomosaic_path = str(ortho_path)
        survey.orthomosaic_filename = f"orthomosaic_srv_{survey.id}.png"

    survey.status = SurveyStatus.PROCESSING.value
    survey.processing_progress = 5
    survey.current_step = "Pipeline initialized"
    db.commit()

    background_tasks.add_task(run_survey_pipeline, survey.id)

    return {
        "message": "Survey AI pipeline started in background",
        "survey_id": survey.id,
        "status": survey.status
    }

@router.get("/{survey_id}/status")
def get_survey_status(
    survey_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")

    return {
        "survey_id": survey.id,
        "status": survey.status,
        "progress": survey.processing_progress or 0,
        "current_step": survey.current_step or "Idle",
        "logs": survey.processing_logs or []
    }

@router.get("/{survey_id}/statistics", response_model=SurveyStatisticsResponse)
def get_survey_statistics(
    survey_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")

    parcels = db.query(Parcel).filter(Parcel.survey_id == survey.id).all()
    features = db.query(CadastralFeature).filter(CadastralFeature.survey_id == survey.id).all()
    discrepancies = db.query(BoundaryChange).filter(BoundaryChange.survey_id == survey.id).all()

    total_p = len(parcels)
    verified_p = sum(1 for p in parcels if p.status == ParcelStatus.VERIFIED.value)
    rejected_p = sum(1 for p in parcels if p.status == ParcelStatus.REJECTED.value)
    pending_p = sum(1 for p in parcels if p.status in [ParcelStatus.PENDING_REVIEW.value, ParcelStatus.FLAGGED_DISCREPANCY.value])

    total_sqm = sum(p.area for p in parcels)
    total_acres = sum(p.area_acres for p in parcels)
    avg_conf = (sum(p.confidence for p in parcels) / total_p) if total_p > 0 else 0.0

    # Land use breakdown
    lu_dict = {}
    for p in parcels:
        lu_dict[p.land_use] = lu_dict.get(p.land_use, 0) + 1

    # Feature breakdown
    feat_dict = {}
    for f in features:
        feat_dict[f.feature_type] = feat_dict.get(f.feature_type, 0) + 1

    return {
        "survey_id": survey.id,
        "survey_name": survey.name,
        "status": survey.status,
        "total_parcels": total_p,
        "verified_parcels": verified_p,
        "rejected_parcels": rejected_p,
        "pending_parcels": pending_p,
        "discrepancy_count": len(discrepancies),
        "total_area_acres": round(total_acres, 2),
        "total_area_sqm": round(total_sqm, 2),
        "average_confidence": round(avg_conf, 4),
        "land_use_summary": lu_dict,
        "feature_counts": feat_dict
    }

@router.post("/load-demo", response_model=SurveyResponse)
def load_sih_demo_survey(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """One-click provision of SIH 2026 Ramnagar Village full demo dataset."""
    survey = seed_demo_dataset(db, force_reset=True)
    p_count = db.query(Parcel).filter(Parcel.survey_id == survey.id).count()
    v_count = db.query(Parcel).filter(Parcel.survey_id == survey.id, Parcel.status == "verified").count()
    d_count = db.query(BoundaryChange).filter(BoundaryChange.survey_id == survey.id).count()

    return {
        "id": survey.id,
        "name": survey.name,
        "village": survey.village,
        "mandal": survey.mandal,
        "district": survey.district,
        "state": survey.state,
        "survey_date": survey.survey_date,
        "survey_officer": survey.survey_officer,
        "description": survey.description,
        "status": survey.status,
        "processing_progress": survey.processing_progress,
        "current_step": survey.current_step,
        "orthomosaic_filename": survey.orthomosaic_filename,
        "cadastral_filename": survey.cadastral_filename,
        "created_at": survey.created_at,
        "updated_at": survey.updated_at,
        "parcel_count": p_count,
        "verified_count": v_count,
        "discrepancy_count": d_count
    }
