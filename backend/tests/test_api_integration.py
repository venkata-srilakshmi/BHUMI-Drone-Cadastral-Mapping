import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from main import app
from app.database.session import Base, engine, SessionLocal
from app.auth.security import init_demo_users
from app.services.demo_data import seed_demo_dataset
from app.models.models import Parcel

class TestApiIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        init_demo_users(db)
        survey = seed_demo_dataset(db)
        cls.survey_id = survey.id
        p103 = db.query(Parcel).filter(Parcel.survey_id == survey.id, Parcel.parcel_id == "P-103").first()
        cls.test_parcel_id = p103.id if p103 else 1
        db.close()
        
        cls.client = TestClient(app)
        # Login to obtain token
        res = cls.client.post("/api/auth/login", json={
            "email": "officer@bhoomi.gov.in",
            "password": "Officer@2026"
        })
        cls.token = res.json()["access_token"]

    def test_root_endpoint(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["platform"], "BHOOMI-AI")

    def test_auth_login_survey_officer(self):
        res = self.client.post("/api/auth/login", json={
            "email": "officer@bhoomi.gov.in",
            "password": "Officer@2026"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["user"]["role"], "survey_officer")
        TestApiIntegration.token = data["access_token"]

    def test_get_surveys(self):
        headers = {"Authorization": f"Bearer {TestApiIntegration.token}"}
        res = self.client.get("/api/surveys", headers=headers)
        self.assertEqual(res.status_code, 200)
        surveys = res.json()
        self.assertGreater(len(surveys), 0)
        TestApiIntegration.survey_id = surveys[0]["id"]

    def test_get_parcels_and_inspect_discrepancy(self):
        headers = {"Authorization": f"Bearer {TestApiIntegration.token}"}
        res = self.client.get(f"/api/surveys/{TestApiIntegration.survey_id}/parcels", headers=headers)
        self.assertEqual(res.status_code, 200)
        parcels = res.json()
        self.assertGreater(len(parcels), 0)
        # Check P-103 has discrepancy
        p103 = next((p for p in parcels if p["parcel_id"] == "P-103"), None)
        self.assertIsNotNone(p103)
        self.assertIsNotNone(p103["discrepancy"])
        self.assertGreater(p103["discrepancy"]["difference_distance"], 1.0)
        TestApiIntegration.test_parcel_id = p103["id"]

    def test_human_in_the_loop_boundary_edit(self):
        headers = {"Authorization": f"Bearer {TestApiIntegration.token}"}
        # Update coordinates slightly to simulate officer adjusting vertices
        new_coords = [
            [78.2910, 17.1536], [78.2934, 17.1536], [78.2934, 17.1515],
            [78.2910, 17.1515], [78.2910, 17.1536]
        ]
        res = self.client.put(
            f"/api/parcels/{TestApiIntegration.test_parcel_id}/geometry",
            headers=headers,
            json={
                "geometry": {"type": "Polygon", "coordinates": [new_coords]},
                "reason": "Officer adjusted boundary to align with physical stone bund verified on-site."
            }
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("original_geometry", data) # immutable original kept!

    def test_verify_parcel(self):
        headers = {"Authorization": f"Bearer {TestApiIntegration.token}"}
        res = self.client.post(
            f"/api/parcels/{TestApiIntegration.test_parcel_id}/verify",
            headers=headers,
            json={"status": "verified", "reason": "Officer approved after physical boundary inspection"}
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "verified")

    def test_ai_spatial_assistant_query(self):
        headers = {"Authorization": f"Bearer {TestApiIntegration.token}"}
        res = self.client.post(
            f"/api/surveys/{TestApiIntegration.survey_id}/ai-query",
            headers=headers,
            json={"query": "Show buildings inside agricultural parcels"}
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("matched_parcel_ids", data)
        self.assertIn("summary_message", data)

    def test_dashboard_analytics(self):
        headers = {"Authorization": f"Bearer {TestApiIntegration.token}"}
        res = self.client.get("/api/analytics/dashboard", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("kpis", data)
        self.assertIn("charts", data)

if __name__ == "__main__":
    unittest.main()
