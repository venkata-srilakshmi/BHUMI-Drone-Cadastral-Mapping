from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database.session import get_db
from app.models.models import CadastralFeature, BoundaryChange
from app.schemas.schemas import CadastralFeatureResponse, BoundaryChangeResponse
from app.auth.security import get_current_user

router = APIRouter(prefix="/surveys", tags=["Features & Discrepancies"])

@router.get("/{survey_id}/features", response_model=List[CadastralFeatureResponse])
def get_survey_features(
    survey_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return db.query(CadastralFeature).filter(CadastralFeature.survey_id == survey_id).all()

@router.get("/{survey_id}/discrepancies", response_model=List[BoundaryChangeResponse])
def get_survey_discrepancies(
    survey_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return db.query(BoundaryChange).filter(BoundaryChange.survey_id == survey_id).all()
