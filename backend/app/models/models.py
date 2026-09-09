import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON, Enum
)
from sqlalchemy.orm import relationship
from app.database.session import Base
import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    SURVEY_OFFICER = "survey_officer"
    VIEWER = "viewer"

class SurveyStatus(str, enum.Enum):
    DRAFT = "draft"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    VERIFIED = "verified"
    FAILED = "failed"

class ParcelStatus(str, enum.Enum):
    PENDING_REVIEW = "pending_review"
    VERIFIED = "verified"
    REJECTED = "rejected"
    FLAGGED_DISCREPANCY = "flagged_discrepancy"

class DiscrepancyStatus(str, enum.Enum):
    REQUIRES_REVIEW = "requires_review"
    APPROVED_DISCREPANCY = "approved_discrepancy"
    DISMISSED = "dismissed"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default=UserRole.SURVEY_OFFICER.value, nullable=False)
    department = Column(String(150), default="Survey & Land Records")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    surveys = relationship("Survey", back_populates="creator")

class Survey(Base):
    __tablename__ = "surveys"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    village = Column(String(100), nullable=False)
    mandal = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)
    state = Column(String(100), default="Telangana", nullable=False)
    survey_date = Column(String(50), nullable=False)
    survey_officer = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default=SurveyStatus.DRAFT.value, nullable=False)
    
    orthomosaic_path = Column(String(255), nullable=True)
    orthomosaic_filename = Column(String(255), nullable=True)
    cadastral_path = Column(String(255), nullable=True)
    cadastral_filename = Column(String(255), nullable=True)
    
    processing_progress = Column(Integer, default=0)
    current_step = Column(String(100), default="Not started")
    processing_logs = Column(JSON, default=list)
    
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    creator = relationship("User", back_populates="surveys")
    parcels = relationship("Parcel", back_populates="survey", cascade="all, delete-orphan")
    features = relationship("CadastralFeature", back_populates="survey", cascade="all, delete-orphan")
    discrepancies = relationship("BoundaryChange", back_populates="survey", cascade="all, delete-orphan")

class Parcel(Base):
    __tablename__ = "parcels"

    id = Column(Integer, primary_key=True, index=True)
    survey_id = Column(Integer, ForeignKey("surveys.id"), nullable=False)
    parcel_id = Column(String(50), index=True, nullable=False)
    
    # Geometry in GeoJSON structure (Polygon / MultiPolygon)
    geometry = Column(JSON, nullable=False)
    original_geometry = Column(JSON, nullable=False)  # Immutable AI-detected boundary
    
    area = Column(Float, nullable=False)  # square meters
    area_acres = Column(Float, nullable=False)  # acres
    perimeter = Column(Float, nullable=False)  # meters
    centroid_lat = Column(Float, nullable=False)
    centroid_lon = Column(Float, nullable=False)
    
    confidence = Column(Float, default=0.85, nullable=False)
    status = Column(String(50), default=ParcelStatus.PENDING_REVIEW.value, nullable=False)
    land_use = Column(String(50), default="Agricultural", nullable=False)
    
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    survey = relationship("Survey", back_populates="parcels")
    features = relationship("CadastralFeature", back_populates="parcel")
    verification_history = relationship("VerificationHistory", back_populates="parcel", cascade="all, delete-orphan")
    discrepancy = relationship("BoundaryChange", back_populates="parcel", uselist=False, cascade="all, delete-orphan")

class CadastralFeature(Base):
    __tablename__ = "cadastral_features"

    id = Column(Integer, primary_key=True, index=True)
    survey_id = Column(Integer, ForeignKey("surveys.id"), nullable=False)
    parcel_id = Column(Integer, ForeignKey("parcels.id"), nullable=True)
    
    feature_type = Column(String(50), nullable=False)  # building, road, water_body, agricultural_field, tree_cluster, pathway, boundary_wall, survey_marker
    geometry = Column(JSON, nullable=False)  # GeoJSON representation
    bbox = Column(JSON, nullable=True)  # [min_x, min_y, max_x, max_y]
    confidence = Column(Float, default=0.90, nullable=False)
    properties = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    survey = relationship("Survey", back_populates="features")
    parcel = relationship("Parcel", back_populates="features")

class BoundaryChange(Base):
    __tablename__ = "boundary_changes"

    id = Column(Integer, primary_key=True, index=True)
    survey_id = Column(Integer, ForeignKey("surveys.id"), nullable=False)
    parcel_id = Column(Integer, ForeignKey("parcels.id"), nullable=False)
    legacy_cadastral_id = Column(String(50), nullable=True)
    
    old_geometry = Column(JSON, nullable=False)  # Legacy Cadastral Polygon
    new_geometry = Column(JSON, nullable=False)  # Drone AI / Adjusted Polygon
    
    difference_area = Column(Float, default=0.0)  # sq meters
    difference_acres = Column(Float, default=0.0)
    difference_percentage = Column(Float, default=0.0)
    difference_distance = Column(Float, default=0.0)  # boundary displacement in meters
    overlap_ratio = Column(Float, default=1.0)
    
    discrepancy_type = Column(String(100), default="Potential Boundary Displacement")
    status = Column(String(50), default=DiscrepancyStatus.REQUIRES_REVIEW.value, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    survey = relationship("Survey", back_populates="discrepancies")
    parcel = relationship("Parcel", back_populates="discrepancy")

class VerificationHistory(Base):
    __tablename__ = "verification_history"

    id = Column(Integer, primary_key=True, index=True)
    parcel_id = Column(Integer, ForeignKey("parcels.id"), nullable=False)
    action = Column(String(50), nullable=False)  # VERIFY, REJECT, EDIT_GEOMETRY, FLAG_DISCREPANCY
    
    old_geometry = Column(JSON, nullable=True)
    new_geometry = Column(JSON, nullable=True)
    
    user_id = Column(Integer, nullable=True)
    user_name = Column(String(100), default="Authorized Officer")
    reason = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    parcel = relationship("Parcel", back_populates="verification_history")

class ChangeDetectionRun(Base):
    __tablename__ = "change_detection_runs"

    id = Column(Integer, primary_key=True, index=True)
    survey_a_id = Column(Integer, nullable=False)
    survey_b_id = Column(Integer, nullable=False)
    survey_a_name = Column(String(150), nullable=True)
    survey_b_name = Column(String(150), nullable=True)
    
    new_buildings_count = Column(Integer, default=0)
    removed_structures_count = Column(Integer, default=0)
    boundary_changes_count = Column(Integer, default=0)
    landuse_changes_count = Column(Integer, default=0)
    
    change_summary = Column(JSON, default=dict)
    change_geojson = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
