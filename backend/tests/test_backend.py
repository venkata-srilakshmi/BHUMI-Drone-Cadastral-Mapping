import unittest
import json
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shapely.geometry import Polygon, mapping
from app.gis.geometry_utils import (
    compute_metric_properties, simplify_and_heal_geometry, compute_boundary_displacement
)
from app.gis.discrepancy import analyze_cadastral_discrepancy
from app.auth.security import get_password_hash, verify_password, create_access_token
from app.services.export import export_parcels_geojson, export_parcels_csv, export_parcels_kml
from app.services.reports import generate_survey_pdf_report
from app.models.models import Survey, Parcel, CadastralFeature, BoundaryChange

class TestGisEngine(unittest.TestCase):
    def setUp(self):
        # Sample polygon in Hyderabad / Rangareddy coordinates
        self.sample_coords = [
            [78.2910, 17.1555], [78.2935, 17.1555], [78.2935, 17.1538],
            [78.2910, 17.1538], [78.2910, 17.1555]
        ]
        self.sample_geom = {"type": "Polygon", "coordinates": [self.sample_coords]}

    def test_area_and_perimeter_calculation(self):
        props = compute_metric_properties(self.sample_geom)
        self.assertGreater(props["area_sqm"], 1000)
        self.assertGreater(props["area_acres"], 0.1)
        self.assertGreater(props["perimeter_m"], 100)
        self.assertAlmostEqual(props["centroid_lat"], 17.15465, places=3)
        self.assertAlmostEqual(props["centroid_lon"], 78.29225, places=3)

    def test_geometry_healing_and_simplification(self):
        healed = simplify_and_heal_geometry(self.sample_geom)
        self.assertEqual(healed["type"], "Polygon")
        self.assertTrue(len(healed["coordinates"][0]) >= 4)

    def test_discrepancy_analysis(self):
        # Shifted polygon representing a 2.5m displacement
        shifted_coords = [
            [78.2910, 17.1555], [78.29353, 17.1555], [78.29353, 17.1538],
            [78.2910, 17.1538], [78.2910, 17.1555]
        ]
        shifted_geom = {"type": "Polygon", "coordinates": [shifted_coords]}
        res = analyze_cadastral_discrepancy(self.sample_geom, shifted_geom)
        
        self.assertIn("boundary_displacement_m", res)
        self.assertGreater(res["boundary_displacement_m"], 0.0)
        self.assertIn("screening_summary", res)
        self.assertIn("discrepancy_type", res)
        self.assertTrue("Screening Result" in res["screening_summary"])

class TestAuthSecurity(unittest.TestCase):
    def test_password_hashing(self):
        pwd = "SurveyOfficer@2026"
        hashed = get_password_hash(pwd)
        self.assertTrue(verify_password(pwd, hashed))
        self.assertFalse(verify_password("WrongPassword", hashed))

    def test_jwt_token_generation(self):
        token = create_access_token({"sub": "officer@bhoomi.gov.in", "role": "survey_officer"})
        self.assertIsInstance(token, str)
        self.assertTrue(len(token) > 20)

class TestExportAndReports(unittest.TestCase):
    def setUp(self):
        self.survey = Survey(
            id=1,
            name="Test Survey 2026",
            village="Ramnagar",
            mandal="Kothur",
            district="Rangareddy",
            state="Telangana",
            survey_date="2026-03-08",
            survey_officer="K. Rajeshwar Rao",
            status="completed"
        )
        geom = {
            "type": "Polygon",
            "coordinates": [[[78.2910, 17.1555], [78.2935, 17.1555], [78.2935, 17.1538], [78.2910, 17.1538], [78.2910, 17.1555]]]
        }
        self.parcel = Parcel(
            id=1,
            survey_id=1,
            parcel_id="P-101",
            geometry=geom,
            original_geometry=geom,
            area=4046.86,
            area_acres=1.0,
            perimeter=260.0,
            centroid_lat=17.15465,
            centroid_lon=78.29225,
            confidence=0.96,
            status="verified",
            land_use="Agricultural"
        )

    def test_geojson_export(self):
        data = export_parcels_geojson([self.parcel], self.survey)
        self.assertEqual(data["type"], "FeatureCollection")
        self.assertEqual(len(data["features"]), 1)
        self.assertEqual(data["features"][0]["properties"]["parcel_id"], "P-101")

    def test_csv_export(self):
        csv_str = export_parcels_csv([self.parcel], self.survey)
        self.assertIn("Parcel ID", csv_str)
        self.assertIn("P-101", csv_str)
        self.assertIn("Ramnagar", csv_str)

    def test_kml_export(self):
        kml_str = export_parcels_kml([self.parcel], self.survey)
        self.assertIn("<kml", kml_str)
        self.assertIn("<Placemark>", kml_str)
        self.assertIn("P-101", kml_str)

    def test_pdf_report_generation(self):
        pdf_bytes = generate_survey_pdf_report(self.survey, [self.parcel], [], [])
        self.assertTrue(len(pdf_bytes) > 500)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

if __name__ == "__main__":
    unittest.main()
