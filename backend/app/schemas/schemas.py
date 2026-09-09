from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime

# --- Auth Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None

class LoginRequest(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    department: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- Survey Schemas ---
class SurveyCreate(BaseModel):
    name: str = Field(..., example="Survey 2026 - Ramnagar North")
    village: str = Field(..., example="Ramnagar")
    mandal: str = Field(..., example="Kothur")
    district: str = Field(..., example="Rangareddy")
    state: str = Field(default="Telangana", example="Telangana")
    survey_date: str = Field(..., example="2026-03-15")
    survey_officer: str = Field(..., example="K. Rajeshwar Rao, Dy. Inspector")
    description: Optional[str] = None

class SurveyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class SurveyResponse(BaseModel):
    id: int
    name: str
    village: str
    mandal: str
    district: str
    state: str
    survey_date: str
    survey_officer: str
    description: Optional[str]
    status: str
    processing_progress: int
    current_step: str
    orthomosaic_filename: Optional[str]
    cadastral_filename: Optional[str]
    created_at: datetime
    updated_at: datetime
    parcel_count: Optional[int] = 0
    verified_count: Optional[int] = 0
    discrepancy_count: Optional[int] = 0

    class Config:
        from_attributes = True

# --- Parcel Schemas ---
class ParcelResponse(BaseModel):
    id: int
    survey_id: int
    parcel_id: str
    geometry: dict
    original_geometry: dict
    area: float
    area_acres: float
    perimeter: float
    centroid_lat: float
    centroid_lon: float
    confidence: float
    status: str
    land_use: str
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    discrepancy: Optional[dict] = None

    class Config:
        from_attributes = True

class ParcelGeometryUpdate(BaseModel):
    geometry: dict
    reason: str = Field(..., min_length=5, description="Official justification for adjusting AI-detected boundary")

class ParcelVerification(BaseModel):
    status: str = Field(..., example="verified")
    reason: Optional[str] = "Inspected and confirmed by Survey Officer"

class VerificationHistoryResponse(BaseModel):
    id: int
    parcel_id: int
    action: str
    old_geometry: Optional[dict]
    new_geometry: Optional[dict]
    user_name: str
    reason: str
    timestamp: datetime

    class Config:
        from_attributes = True

# --- Cadastral Feature Schemas ---
class CadastralFeatureResponse(BaseModel):
    id: int
    survey_id: int
    parcel_id: Optional[int]
    feature_type: str
    geometry: dict
    bbox: Optional[list]
    confidence: float
    properties: Optional[dict]

    class Config:
        from_attributes = True

# --- Boundary Discrepancy Schemas ---
class BoundaryChangeResponse(BaseModel):
    id: int
    survey_id: int
    parcel_id: int
    legacy_cadastral_id: Optional[str]
    old_geometry: dict
    new_geometry: dict
    difference_area: float
    difference_acres: float
    difference_percentage: float
    difference_distance: float
    overlap_ratio: float
    discrepancy_type: str
    status: str
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# --- AI Assistant Query Schemas ---
class SpatialQueryRequest(BaseModel):
    query: str = Field(..., example="Show buildings inside agricultural parcels")

class SpatialQueryResponse(BaseModel):
    query: str
    interpreted_intent: str
    matched_parcel_ids: list[str]
    matched_feature_ids: list[int]
    summary_message: str
    count: int

# --- Change Detection Schemas ---
class ChangeDetectionRequest(BaseModel):
    survey_a_id: int
    survey_b_id: int

class ChangeDetectionResponse(BaseModel):
    id: int
    survey_a_id: int
    survey_b_id: int
    survey_a_name: str
    survey_b_name: str
    new_buildings_count: int
    removed_structures_count: int
    boundary_changes_count: int
    landuse_changes_count: int
    change_summary: dict
    change_geojson: dict
    created_at: datetime

    class Config:
        from_attributes = True

# --- Reports & Survey Statistics Schemas ---
class ReportGenerateRequest(BaseModel):
    survey_id: int
    format: Optional[str] = "pdf"

class SurveyStatisticsResponse(BaseModel):
    survey_id: int
    survey_name: str
    status: str
    total_parcels: int
    verified_parcels: int
    rejected_parcels: int
    pending_parcels: int
    discrepancy_count: int
    total_area_acres: float
    total_area_sqm: float
    average_confidence: float
    land_use_summary: dict
    feature_counts: dict

