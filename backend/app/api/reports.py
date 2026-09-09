from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io
import json
from typing import Optional

from app.database.session import get_db
from app.models.models import Survey, Parcel, CadastralFeature, BoundaryChange
from app.schemas.schemas import ReportGenerateRequest
from app.services.reports import generate_survey_pdf_report
from app.services.export import export_parcels_geojson, export_parcels_csv, export_parcels_kml
from app.auth.security import get_current_user

router = APIRouter(tags=["Reports & Exports"])

@router.get("/surveys/{survey_id}/report")
def download_survey_report_pdf(
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

    pdf_bytes = generate_survey_pdf_report(survey, parcels, features, discrepancies)

    filename = f"BHOOMI_AI_Dossier_SRV_{survey.id:04d}_{survey.village}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/surveys/{survey_id}/export/{export_format}")
def export_survey_data(
    survey_id: int,
    export_format: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")

    parcels = db.query(Parcel).filter(Parcel.survey_id == survey.id).all()

    fmt = export_format.lower()
    if fmt == "geojson":
        data = export_parcels_geojson(parcels, survey)
        filename = f"parcels_srv_{survey.id:04d}_{survey.village}.geojson"
        return Response(
            content=json.dumps(data, indent=2),
            media_type="application/geo+json",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    elif fmt == "csv":
        csv_text = export_parcels_csv(parcels, survey)
        filename = f"parcel_register_srv_{survey.id:04d}_{survey.village}.csv"
        return Response(
            content=csv_text,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    elif fmt == "kml":
        kml_text = export_parcels_kml(parcels, survey)
        filename = f"parcels_srv_{survey.id:04d}_{survey.village}.kml"
        return Response(
            content=kml_text,
            media_type="application/vnd.google-earth.kml+xml",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported export format '{export_format}'. Supported: geojson, csv, kml")

@router.post("/reports/generate")
def generate_report(
    req: ReportGenerateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Contract endpoint to generate reports or exports for a survey.
    Accepts { "survey_id": int, "format": "pdf" | "geojson" | "csv" | "kml" }.
    """
    fmt = (req.format or "pdf").lower()
    if fmt == "pdf":
        return download_survey_report_pdf(req.survey_id, db, current_user)
    else:
        return export_survey_data(req.survey_id, fmt, db, current_user)
