from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.session import get_db
from app.models.models import Parcel, BoundaryChange, VerificationHistory, ParcelStatus
from app.schemas.schemas import (
    ParcelResponse, ParcelGeometryUpdate, ParcelVerification, VerificationHistoryResponse
)
from app.auth.security import get_current_user, require_roles
from app.gis.geometry_utils import compute_metric_properties, simplify_and_heal_geometry
from app.gis.discrepancy import analyze_cadastral_discrepancy

router = APIRouter(tags=["Parcels"])

def _format_parcel(p: Parcel) -> dict:
    d_dict = None
    if p.discrepancy:
        d_dict = {
            "id": p.discrepancy.id,
            "legacy_cadastral_id": p.discrepancy.legacy_cadastral_id,
            "difference_distance": p.discrepancy.difference_distance,
            "difference_acres": p.discrepancy.difference_acres,
            "difference_percentage": p.discrepancy.difference_percentage,
            "discrepancy_type": p.discrepancy.discrepancy_type,
            "status": p.discrepancy.status,
            "notes": p.discrepancy.notes,
            "old_geometry": p.discrepancy.old_geometry
        }
    return {
        "id": p.id,
        "survey_id": p.survey_id,
        "parcel_id": p.parcel_id,
        "geometry": p.geometry,
        "original_geometry": p.original_geometry,
        "area": p.area,
        "area_acres": p.area_acres,
        "perimeter": p.perimeter,
        "centroid_lat": p.centroid_lat,
        "centroid_lon": p.centroid_lon,
        "confidence": p.confidence,
        "status": p.status,
        "land_use": p.land_use,
        "notes": p.notes,
        "created_at": p.created_at,
        "updated_at": p.updated_at,
        "discrepancy": d_dict
    }

@router.get("/surveys/{survey_id}/parcels", response_model=List[ParcelResponse])
def get_survey_parcels(
    survey_id: int,
    status_filter: Optional[str] = None,
    confidence_tier: Optional[str] = None,
    land_use: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(Parcel).filter(Parcel.survey_id == survey_id)

    if status_filter:
        query = query.filter(Parcel.status == status_filter)

    if confidence_tier == "high":
        query = query.filter(Parcel.confidence >= 0.95)
    elif confidence_tier == "medium":
        query = query.filter(Parcel.confidence >= 0.80, Parcel.confidence < 0.95)
    elif confidence_tier == "low":
        query = query.filter(Parcel.confidence < 0.80)

    if land_use:
        query = query.filter(Parcel.land_use.ilike(f"%{land_use}%"))

    parcels = query.order_by(Parcel.id.asc()).all()

    res = []
    for p in parcels:
        d_dict = None
        if p.discrepancy:
            d_dict = {
                "id": p.discrepancy.id,
                "legacy_cadastral_id": p.discrepancy.legacy_cadastral_id,
                "difference_distance": p.discrepancy.difference_distance,
                "difference_acres": p.discrepancy.difference_acres,
                "difference_percentage": p.discrepancy.difference_percentage,
                "discrepancy_type": p.discrepancy.discrepancy_type,
                "status": p.discrepancy.status,
                "notes": p.discrepancy.notes,
                "old_geometry": p.discrepancy.old_geometry
            }

        res.append({
            "id": p.id,
            "survey_id": p.survey_id,
            "parcel_id": p.parcel_id,
            "geometry": p.geometry,
            "original_geometry": p.original_geometry,
            "area": p.area,
            "area_acres": p.area_acres,
            "perimeter": p.perimeter,
            "centroid_lat": p.centroid_lat,
            "centroid_lon": p.centroid_lon,
            "confidence": p.confidence,
            "status": p.status,
            "land_use": p.land_use,
            "notes": p.notes,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
            "discrepancy": d_dict
        })

    return res

@router.get("/parcels/{parcel_id}", response_model=ParcelResponse)
def get_parcel(
    parcel_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    p = db.query(Parcel).filter(Parcel.id == parcel_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Parcel not found")

    d_dict = None
    if p.discrepancy:
        d_dict = {
            "id": p.discrepancy.id,
            "legacy_cadastral_id": p.discrepancy.legacy_cadastral_id,
            "difference_distance": p.discrepancy.difference_distance,
            "difference_acres": p.discrepancy.difference_acres,
            "difference_percentage": p.discrepancy.difference_percentage,
            "discrepancy_type": p.discrepancy.discrepancy_type,
            "status": p.discrepancy.status,
            "notes": p.discrepancy.notes,
            "old_geometry": p.discrepancy.old_geometry
        }

    return {
        "id": p.id,
        "survey_id": p.survey_id,
        "parcel_id": p.parcel_id,
        "geometry": p.geometry,
        "original_geometry": p.original_geometry,
        "area": p.area,
        "area_acres": p.area_acres,
        "perimeter": p.perimeter,
        "centroid_lat": p.centroid_lat,
        "centroid_lon": p.centroid_lon,
        "confidence": p.confidence,
        "status": p.status,
        "land_use": p.land_use,
        "notes": p.notes,
        "created_at": p.created_at,
        "updated_at": p.updated_at,
        "discrepancy": d_dict
    }

@router.put("/parcels/{parcel_id}/geometry", response_model=ParcelResponse)
def update_parcel_geometry(
    parcel_id: int,
    geom_update: ParcelGeometryUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "survey_officer"]))
):
    """
    Human-in-the-loop boundary adjustment.
    Modifies parcel polygon, recomputes metric area/perimeter, maintains immutable AI baseline,
    and logs verification audit trail.
    """
    parcel = db.query(Parcel).filter(Parcel.id == parcel_id).first()
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")

    old_geometry = parcel.geometry
    healed_new_geom = simplify_and_heal_geometry(geom_update.geometry)
    new_props = compute_metric_properties(healed_new_geom)

    # Update parcel fields
    parcel.geometry = healed_new_geom
    parcel.area = new_props["area_sqm"]
    parcel.area_acres = new_props["area_acres"]
    parcel.perimeter = new_props["perimeter_m"]
    parcel.centroid_lat = new_props["centroid_lat"]
    parcel.centroid_lon = new_props["centroid_lon"]
    parcel.status = ParcelStatus.PENDING_REVIEW.value

    # Record in verification audit history
    history = VerificationHistory(
        parcel_id=parcel.id,
        action="EDIT_GEOMETRY",
        old_geometry=old_geometry,
        new_geometry=healed_new_geom,
        user_id=current_user.id,
        user_name=current_user.name,
        reason=geom_update.reason
    )
    db.add(history)

    # If discrepancy exists, re-evaluate difference against legacy cadastral
    if parcel.discrepancy:
        disc_res = analyze_cadastral_discrepancy(parcel.discrepancy.old_geometry, healed_new_geom)
        parcel.discrepancy.new_geometry = healed_new_geom
        parcel.discrepancy.difference_area = disc_res["difference_sqm"]
        parcel.discrepancy.difference_acres = disc_res["difference_acres"]
        parcel.discrepancy.difference_percentage = disc_res["difference_percentage"]
        parcel.discrepancy.difference_distance = disc_res["boundary_displacement_m"]
        parcel.discrepancy.overlap_ratio = disc_res["overlap_ratio"]
        parcel.discrepancy.notes = f"Updated after officer boundary modification. {disc_res['screening_summary']}"

    db.commit()
    db.refresh(parcel)

    return _format_parcel(parcel)

@router.post("/parcels/{parcel_id}/verify")
def verify_parcel(
    parcel_id: int,
    verification: ParcelVerification,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "survey_officer"]))
):
    parcel = db.query(Parcel).filter(Parcel.id == parcel_id).first()
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")

    parcel.status = ParcelStatus.VERIFIED.value
    
    # Audit trail
    history = VerificationHistory(
        parcel_id=parcel.id,
        action="VERIFY",
        old_geometry=parcel.geometry,
        new_geometry=parcel.geometry,
        user_id=current_user.id,
        user_name=current_user.name,
        reason=verification.reason or "Boundary approved by authorized Survey Officer"
    )
    db.add(history)
    db.commit()

    return {"message": f"Parcel {parcel.parcel_id} verified successfully", "status": parcel.status}

@router.post("/parcels/{parcel_id}/reject")
def reject_parcel(
    parcel_id: int,
    verification: ParcelVerification,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "survey_officer"]))
):
    parcel = db.query(Parcel).filter(Parcel.id == parcel_id).first()
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")

    parcel.status = ParcelStatus.REJECTED.value
    
    # Audit trail
    history = VerificationHistory(
        parcel_id=parcel.id,
        action="REJECT",
        old_geometry=parcel.geometry,
        new_geometry=parcel.geometry,
        user_id=current_user.id,
        user_name=current_user.name,
        reason=verification.reason or "Parcel boundary rejected by Survey Officer"
    )
    db.add(history)
    db.commit()

    return {"message": f"Parcel {parcel.parcel_id} rejected", "status": parcel.status}

@router.get("/parcels/{parcel_id}/history", response_model=List[VerificationHistoryResponse])
def get_parcel_history(
    parcel_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return db.query(VerificationHistory).filter(VerificationHistory.parcel_id == parcel_id).order_by(VerificationHistory.timestamp.desc()).all()
