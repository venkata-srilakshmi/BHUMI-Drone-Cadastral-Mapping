from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.schemas import SpatialQueryRequest, SpatialQueryResponse
from app.gis.spatial_queries import interpret_and_execute_spatial_query
from app.auth.security import get_current_user

router = APIRouter(prefix="/surveys", tags=["AI Assistant"])

@router.post("/{survey_id}/ai-query", response_model=SpatialQueryResponse)
def execute_ai_query(
    survey_id: int,
    req: SpatialQueryRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    result = interpret_and_execute_spatial_query(req.query, survey_id, db)
    return result
