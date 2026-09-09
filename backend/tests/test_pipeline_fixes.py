import unittest
import sys
import os
import json
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from main import app
from app.database.session import Base, engine, SessionLocal
from app.auth.security import init_demo_users, create_access_token
from app.models.models import Survey, SurveyStatus, Parcel, CadastralFeature
from app.ai.feature_detection.detector import CadastralFeatureDetector
from app.gis.validator import (
    validate_orthomosaic_file, validate_cadastral_file, validate_spatial_overlap, DEFAULT_SURVEY_BOUNDS
)
from app.services.pipeline import run_survey_pipeline, _ACTIVE_PIPELINES, _PIPELINE_LOCK

class TestPipelineAndAuthFixes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        init_demo_users(db)
        db.close()
        cls.client = TestClient(app)

    # -------------------------------------------------------------
    # PART 2: AUTHENTICATION TESTS
    # -------------------------------------------------------------
    def test_auth_valid_login(self):
        """Valid login succeeds with JWT and user details."""
        res = self.client.post("/api/auth/login", json={
            "email": "officer@bhoomi.gov.in",
            "password": "Officer@2026"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["user"]["email"], "officer@bhoomi.gov.in")
        self.assertEqual(data["user"]["role"], "survey_officer")

    def test_auth_case_insensitive_and_trimmed(self):
        """Case-insensitive and whitespace-padded email succeeds."""
        res = self.client.post("/api/auth/login", json={
            "email": "  Officer@BHOOMI.GOV.IN  ",
            "password": "Officer@2026"
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn("access_token", res.json())

    def test_auth_username_field(self):
        """Standard username field in JSON succeeds."""
        res = self.client.post("/api/auth/login", json={
            "username": "officer@bhoomi.gov.in",
            "password": "Officer@2026"
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn("access_token", res.json())

    def test_auth_invalid_password(self):
        """Invalid password returns 401."""
        res = self.client.post("/api/auth/login", json={
            "email": "officer@bhoomi.gov.in",
            "password": "WrongPassword123!"
        })
        self.assertEqual(res.status_code, 401)
        self.assertIn("Invalid email or password", res.json()["detail"])

    def test_auth_unknown_user(self):
        """Unknown user returns 401."""
        res = self.client.post("/api/auth/login", json={
            "email": "nonexistent@bhoomi.gov.in",
            "password": "Officer@2026"
        })
        self.assertEqual(res.status_code, 401)
        self.assertIn("Invalid email or password", res.json()["detail"])

    def test_protected_api_without_token(self):
        """Protected endpoint without token returns 401."""
        res = self.client.get("/api/surveys")
        self.assertEqual(res.status_code, 401)

    def test_protected_api_with_invalid_token(self):
        """Protected endpoint with garbage token returns 401."""
        res = self.client.get("/api/surveys", headers={"Authorization": "Bearer invalid.fake.token"})
        self.assertEqual(res.status_code, 401)

    def test_protected_api_with_valid_token(self):
        """Protected endpoint with valid token returns 200."""
        token = create_access_token({"sub": "officer@bhoomi.gov.in", "role": "survey_officer"})
        res = self.client.get("/api/surveys", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(res.status_code, 200)

    # -------------------------------------------------------------
    # PART 3: NUMPY / FEATURE DETECTION FIX
    # -------------------------------------------------------------
    def test_feature_detector_houghlinesp_unpacking(self):
        """
        Verify that CadastralFeatureDetector safely unpacks HoughLinesP
        on actual drone imagery without raising:
        cannot unpack non-iterable numpy.int32 object
        """
        ortho_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "..", "..", "data", "storage", "survey_0002", "input", "Drone orthomosiac.jpg"
        ))
        if os.path.exists(ortho_path):
            detector = CadastralFeatureDetector()
            bounds = (78.2905, 17.1495, 78.2975, 17.1560)
            features = detector.detect_features(ortho_path, bounds)
            self.assertIsInstance(features, list)
            # Ensure road lines or features were detected and unpack was successful
            for f in features:
                self.assertIn("feature_type", f)
                self.assertIn("geometry", f)
                self.assertIn("bbox", f)

    # -------------------------------------------------------------
    # PART 5: INPUT & SPATIAL OVERLAP VALIDATION
    # -------------------------------------------------------------
    def test_validator_rejects_raster_as_cadastral(self):
        """Validator explicitly rejects a raster image uploaded as cadastral vector."""
        img_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "..", "..", "data", "storage", "survey_0002", "input", "img1.jpg"
        ))
        if os.path.exists(img_path):
            with self.assertRaises(ValueError) as ctx:
                validate_cadastral_file(img_path)
            self.assertIn("Raster image files", str(ctx.exception))
            self.assertIn("cannot be parsed as cadastral vector datasets", str(ctx.exception))

    def test_validator_detects_non_overlapping_datasets(self):
        """Validator rejects datasets from different geographical areas with clear error."""
        # Hyderabad/Telangana bounds
        ortho_bounds = (78.2905, 17.1495, 78.2975, 17.1560)
        # Delhi coordinates
        unrelated_cadastral_bounds = (77.1000, 28.6000, 77.1500, 28.6500)

        with self.assertRaises(ValueError) as ctx:
            validate_spatial_overlap(ortho_bounds, unrelated_cadastral_bounds)
        
        err_msg = str(ctx.exception)
        self.assertIn("Drone orthomosaic and cadastral dataset do not overlap geographically", err_msg)
        self.assertIn("Please upload datasets for the same survey area", err_msg)

    def test_validator_accepts_overlapping_datasets(self):
        """Validator accepts matching datasets and computes overlap percentage."""
        ortho_bounds = (78.2905, 17.1495, 78.2975, 17.1560)
        matching_cadastral_bounds = (78.2910, 17.1500, 78.2970, 17.1555)

        res = validate_spatial_overlap(ortho_bounds, matching_cadastral_bounds)
        self.assertTrue(res["overlaps"])
        self.assertGreater(res["overlap_percentage"], 0.0)

    # -------------------------------------------------------------
    # PART 7 & 8: PIPELINE IDEMPOTENCY & STATUS
    # -------------------------------------------------------------
    def test_pipeline_idempotency_locking(self):
        """Ensure active pipeline lock prevents two concurrent jobs for same survey."""
        survey_id = 9999
        with _PIPELINE_LOCK:
            _ACTIVE_PIPELINES.add(survey_id)

        try:
            # Calling pipeline while survey is locked should return immediately
            run_survey_pipeline(survey_id)
            self.assertIn(survey_id, _ACTIVE_PIPELINES)
        finally:
            with _PIPELINE_LOCK:
                _ACTIVE_PIPELINES.discard(survey_id)

    # -------------------------------------------------------------
    # PART 10: API CONTRACT TESTS (STATISTICS & REPORTS)
    # -------------------------------------------------------------
    def test_survey_statistics_endpoint(self):
        """GET /api/surveys/{id}/statistics returns complete survey metrics."""
        token = create_access_token({"sub": "officer@bhoomi.gov.in", "role": "survey_officer"})
        headers = {"Authorization": f"Bearer {token}"}
        
        # Check survey 1
        res = self.client.get("/api/surveys/1/statistics", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["survey_id"], 1)
        self.assertIn("total_parcels", data)
        self.assertIn("verified_parcels", data)
        self.assertIn("discrepancy_count", data)
        self.assertIn("total_area_acres", data)
        self.assertIn("land_use_summary", data)

    def test_reports_generate_endpoint(self):
        """POST /api/reports/generate generates PDF report."""
        token = create_access_token({"sub": "officer@bhoomi.gov.in", "role": "survey_officer"})
        headers = {"Authorization": f"Bearer {token}"}

        res = self.client.post("/api/reports/generate", headers=headers, json={
            "survey_id": 1,
            "format": "pdf"
        })
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers.get("content-type"), "application/pdf")

if __name__ == "__main__":
    unittest.main()
