from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.session import get_db
from app.models.models import Survey, Parcel, CadastralFeature, BoundaryChange
from app.auth.security import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/dashboard")
def get_dashboard_metrics(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    total_surveys = db.query(Survey).count()
    total_parcels = db.query(Parcel).count()
    total_features = db.query(CadastralFeature).count()
    verified_parcels = db.query(Parcel).filter(Parcel.status == "verified").count()
    pending_parcels = db.query(Parcel).filter(Parcel.status.in_(["pending_review", "flagged_discrepancy"])).count()
    total_discrepancies = db.query(BoundaryChange).count()
    low_confidence_parcels = db.query(Parcel).filter(Parcel.confidence < 0.85).count()

    # Total area mapped (acres)
    total_area_acres = db.query(func.sum(Parcel.area_acres)).scalar() or 0.0

    # Land use breakdown
    land_use_counts = (
        db.query(Parcel.land_use, func.count(Parcel.id))
        .group_by(Parcel.land_use)
        .all()
    )
    land_use_chart = [{"name": lu, "value": cnt} for lu, cnt in land_use_counts]

    # Verification status breakdown
    status_counts = (
        db.query(Parcel.status, func.count(Parcel.id))
        .group_by(Parcel.status)
        .all()
    )
    status_chart = [
        {"name": s.replace("_", " ").title(), "value": cnt, "status": s}
        for s, cnt in status_counts
    ]

    # Confidence distribution tiers
    high_conf = db.query(Parcel).filter(Parcel.confidence >= 0.95).count()
    med_conf = db.query(Parcel).filter(Parcel.confidence >= 0.80, Parcel.confidence < 0.95).count()
    low_conf = db.query(Parcel).filter(Parcel.confidence < 0.80).count()
    confidence_tiers = [
        {"tier": "High Confidence (95-100%)", "count": high_conf, "color": "#10b981"},
        {"tier": "Medium Confidence (80-94%)", "count": med_conf, "color": "#f59e0b"},
        {"tier": "Requires Review (<80%)", "count": low_conf, "color": "#ef4444"}
    ]

    # Feature distribution
    feature_counts = (
        db.query(CadastralFeature.feature_type, func.count(CadastralFeature.id))
        .group_by(CadastralFeature.feature_type)
        .all()
    )
    feature_chart = [
        {"name": ft.replace("_", " ").title(), "count": cnt}
        for ft, cnt in feature_counts
    ]

    return {
        "kpis": {
            "total_surveys": total_surveys,
            "total_parcels": total_parcels,
            "total_features": total_features,
            "verified_parcels": verified_parcels,
            "pending_parcels": pending_parcels,
            "total_discrepancies": total_discrepancies,
            "low_confidence_parcels": low_confidence_parcels,
            "total_area_acres": round(float(total_area_acres), 2)
        },
        "charts": {
            "land_use": land_use_chart,
            "verification_status": status_chart,
            "confidence_tiers": confidence_tiers,
            "feature_distribution": feature_chart
        }
    }
