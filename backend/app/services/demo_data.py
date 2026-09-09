import os
import json
import numpy as np
import cv2
from PIL import Image, ImageDraw
from pathlib import Path
from sqlalchemy.orm import Session
from app.config import settings
from app.models.models import (
    Survey, Parcel, CadastralFeature, BoundaryChange, VerificationHistory, ChangeDetectionRun,
    SurveyStatus, ParcelStatus, DiscrepancyStatus
)
from app.gis.geometry_utils import compute_metric_properties, compute_boundary_displacement

# Geographic bounding box for Ramnagar Village prototype (near Kothur, Telangana)
# Coordinates: Lat ~17.150 to 17.156, Lon ~78.290 to 78.298
BASE_LAT = 17.1520
BASE_LON = 78.2930

def generate_synthetic_orthomosaic(output_path: Path):
    """
    Generates a high-quality 1024x1024 realistic synthetic aerial orthomosaic
    depicting agricultural field parcels, village abadi (settlement),
    an access road, water reservoir, and green field bunds.
    """
    img = np.zeros((1024, 1024, 3), dtype=np.uint8)

    # 1. Base terrain / soil variations
    # Greenish-tan agricultural soil
    img[:, :] = (85, 135, 110) # BGR
    
    # Add Perlin/Gaussian texture for realistic aerial terrain look
    noise = np.random.normal(0, 12, (1024, 1024, 3)).astype(np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    # 2. Agricultural parcels (rectangles with varying crops / fallow fields)
    fields = [
        ((40, 40), (450, 420), (60, 140, 95)),    # Lush green paddy
        ((470, 40), (980, 420), (50, 110, 150)),  # Dry fallow field
        ((40, 460), (320, 980), (70, 160, 120)),  # Cotton crop
        ((350, 460), (680, 980), (80, 125, 160)), # Mustard field
        ((710, 620), (980, 980), (45, 130, 80)),  # Horticulture plot
    ]
    for top_left, bot_right, col in fields:
        cv2.rectangle(img, top_left, bot_right, col, -1)
        # Inner furrow lines
        for y in range(top_left[1] + 15, bot_right[1], 20):
            cv2.line(img, (top_left[0] + 5, y), (bot_right[0] - 5, y), (col[0]-15, col[1]-15, col[2]-15), 1)

    # 3. Water reservoir / irrigation tank
    cv2.ellipse(img, (840, 520), (120, 80), 20, 0, 360, (180, 130, 40), -1) # Deep cyan/blue
    cv2.ellipse(img, (840, 520), (125, 85), 20, 0, 360, (140, 100, 30), 3)

    # 4. Village arterial road (Grey asphalt line running through)
    road_pts = np.array([[0, 435], [460, 435], [490, 455], [700, 600], [1024, 600]], dtype=np.int32)
    cv2.polylines(img, [road_pts], False, (110, 110, 110), 18)
    cv2.polylines(img, [road_pts], False, (220, 220, 220), 2) # Center line

    # Secondary pathway
    path_pts = np.array([[460, 0], [460, 1024]], dtype=np.int32)
    cv2.polylines(img, [path_pts], False, (90, 120, 140), 10)

    # 5. Buildings / Rural Homesteads
    homesteads = [
        (510, 490, 60, 40),
        (590, 500, 50, 45),
        (530, 560, 70, 50),
        (620, 565, 45, 35),
        (200, 150, 55, 40), # Farm house
        (270, 160, 40, 30), # Shed
    ]
    for x, y, w, h in homesteads:
        # Building shadow
        cv2.rectangle(img, (x+4, y+4), (x+w+4, y+h+4), (30, 40, 30), -1)
        # Red/terracotta tile roof
        cv2.rectangle(img, (x, y), (x+w, y+h), (50, 60, 170), -1)
        # Ridge line
        cv2.line(img, (x, y+h//2), (x+w, y+h//2), (70, 80, 200), 2)

    # 6. Green field bunds / boundary hedges
    for top_left, bot_right, _ in fields:
        cv2.rectangle(img, top_left, bot_right, (30, 70, 40), 3)

    cv2.imwrite(str(output_path), img)

def create_raw_demo_parcels() -> list[dict]:
    """Generates 10 realistic parcels in EPSG:4326 around Ramnagar."""
    # Scale: 0.001 deg lat ~ 111m, 0.001 deg lon ~ 106m
    parcels_raw = [
        {
            "parcel_id": "P-101",
            "coords": [
                [78.2910, 17.1555], [78.2935, 17.1555], [78.2935, 17.1538],
                [78.2910, 17.1538], [78.2910, 17.1555]
            ],
            "land_use": "Agricultural (Paddy)",
            "confidence": 0.96,
            "status": "verified"
        },
        {
            "parcel_id": "P-102",
            "coords": [
                [78.2937, 17.1555], [78.2965, 17.1555], [78.2965, 17.1538],
                [78.2937, 17.1538], [78.2937, 17.1555]
            ],
            "land_use": "Agricultural (Fallow)",
            "confidence": 0.94,
            "status": "verified"
        },
        {
            "parcel_id": "P-103",
            "coords": [
                [78.2910, 17.1536], [78.2935, 17.1536], [78.2935, 17.1515],
                [78.2910, 17.1515], [78.2910, 17.1536]
            ],
            "land_use": "Agricultural (Cotton)",
            "confidence": 0.82,
            "status": "flagged_discrepancy"
        },
        {
            "parcel_id": "P-104",
            "coords": [
                [78.2937, 17.1536], [78.2952, 17.1536], [78.2952, 17.1515],
                [78.2937, 17.1515], [78.2937, 17.1536]
            ],
            "land_use": "Residential (Abadi/Homestead)",
            "confidence": 0.91,
            "status": "pending_review"
        },
        {
            "parcel_id": "P-105",
            "coords": [
                [78.2954, 17.1536], [78.2968, 17.1536], [78.2968, 17.1524],
                [78.2954, 17.1524], [78.2954, 17.1536]
            ],
            "land_use": "Commercial (Village Agro-Center)",
            "confidence": 0.88,
            "status": "pending_review"
        },
        {
            "parcel_id": "P-106",
            "coords": [
                [78.2954, 17.1522], [78.2968, 17.1522], [78.2968, 17.1515],
                [78.2954, 17.1515], [78.2954, 17.1522]
            ],
            "land_use": "Water Body (Village Pond)",
            "confidence": 0.98,
            "status": "verified"
        },
        {
            "parcel_id": "P-107",
            "coords": [
                [78.2925, 17.1513], [78.2948, 17.1513], [78.2948, 17.1498],
                [78.2925, 17.1498], [78.2925, 17.1513]
            ],
            "land_use": "Agricultural (Horticulture)",
            "confidence": 0.79,
            "status": "flagged_discrepancy"
        },
        {
            "parcel_id": "P-108",
            "coords": [
                [78.2950, 17.1513], [78.2968, 17.1513], [78.2968, 17.1498],
                [78.2950, 17.1498], [78.2950, 17.1513]
            ],
            "land_use": "Agricultural (Mustard)",
            "confidence": 0.92,
            "status": "pending_review"
        }
    ]
    return parcels_raw

def seed_demo_dataset(db: Session, force_reset: bool = False) -> Survey:
    """
    Seeds a full-scale prototype survey with realistic parcels, cadastral discrepancies,
    features, and verification history.
    """
    existing = db.query(Survey).filter(Survey.name == "Ramnagar Village Cadastral Survey 2026").first()
    if existing and not force_reset:
        return existing
    if existing and force_reset:
        db.delete(existing)
        db.commit()

    # 1. Create Survey record
    survey = Survey(
        name="Ramnagar Village Cadastral Survey 2026",
        village="Ramnagar",
        mandal="Kothur",
        district="Rangareddy",
        state="Telangana",
        survey_date="2026-03-08",
        survey_officer="K. Rajeshwar Rao, Dy. Inspector of Survey",
        description=(
            "High-resolution drone orthomosaic survey conducted under the Digital India Land Records "
            "Modernization Programme (DILRMP) and SVAMITVA scheme. Includes AI automated parcel boundary "
            "extraction, feature identification, and legacy revenue map cross-validation."
        ),
        status=SurveyStatus.COMPLETED.value,
        processing_progress=100,
        current_step="Processing completed",
        orthomosaic_filename="orthomosaic_ramnagar_sih2026.png",
        cadastral_filename="cadastral_ramnagar_1984.geojson",
        created_by=1
    )
    db.add(survey)
    db.flush()

    # Create synthetic imagery file
    ortho_dir = settings.STORAGE_PATH / f"survey_{survey.id:04d}" / "processed"
    os.makedirs(ortho_dir, exist_ok=True)
    ortho_path = ortho_dir / "orthomosaic_ramnagar_sih2026.png"
    if not ortho_path.exists():
        generate_synthetic_orthomosaic(ortho_path)
    survey.orthomosaic_path = str(ortho_path)

    # 2. Add Parcels & Features
    raw_parcels = create_raw_demo_parcels()
    saved_parcels = []

    for item in raw_parcels:
        geom = {
            "type": "Polygon",
            "coordinates": [item["coords"]]
        }
        props = compute_metric_properties(geom)

        p = Parcel(
            survey_id=survey.id,
            parcel_id=item["parcel_id"],
            geometry=geom,
            original_geometry=geom,
            area=props["area_sqm"],
            area_acres=props["area_acres"],
            perimeter=props["perimeter_m"],
            centroid_lat=props["centroid_lat"],
            centroid_lon=props["centroid_lon"],
            confidence=item["confidence"],
            status=item["status"],
            land_use=item["land_use"],
            notes=f"AI Candidate Boundary for {item['parcel_id']} - {item['land_use']}"
        )
        db.add(p)
        db.flush()
        saved_parcels.append((p, item["coords"]))

    # 3. Add Boundary Discrepancies (Legacy Cadastral vs AI Drone)
    # Discrepancy for P-103: 2.4 meter field bund shift on the eastern boundary
    p103, c103 = next(x for x in saved_parcels if x[0].parcel_id == "P-103")
    legacy_coords_p103 = [
        [78.2910, 17.1536], [78.2933, 17.1536], [78.2933, 17.1515], # Legacy eastern edge shifted by ~2.4m westward
        [78.2910, 17.1515], [78.2910, 17.1536]
    ]
    legacy_geom_p103 = {"type": "Polygon", "coordinates": [legacy_coords_p103]}
    leg_props_103 = compute_metric_properties(legacy_geom_p103)
    disp_103 = compute_boundary_displacement(legacy_geom_p103, p103.geometry)

    disc_103 = BoundaryChange(
        survey_id=survey.id,
        parcel_id=p103.id,
        legacy_cadastral_id="LEG-KOT-103",
        old_geometry=legacy_geom_p103,
        new_geometry=p103.geometry,
        difference_area=round(abs(p103.area - leg_props_103["area_sqm"]), 2),
        difference_acres=round(abs(p103.area_acres - leg_props_103["area_acres"]), 4),
        difference_percentage=round((abs(p103.area_acres - leg_props_103["area_acres"]) / max(leg_props_103["area_acres"], 0.001)) * 100, 2),
        difference_distance=disp_103,
        overlap_ratio=0.91,
        discrepancy_type="Potential Eastern Field Bund Displacement (2.4m shift)",
        status=DiscrepancyStatus.REQUIRES_REVIEW.value,
        notes="Screening Result: AI drone imagery indicates field bund was shifted 2.4m east into fallow land. Requires officer ground inspection."
    )
    db.add(disc_103)

    # Discrepancy for P-107: Road widening encroachment (1.8 meter shift)
    p107, c107 = next(x for x in saved_parcels if x[0].parcel_id == "P-107")
    legacy_coords_p107 = [
        [78.2925, 17.15145], [78.2948, 17.15145], [78.2948, 17.1498],
        [78.2925, 17.1498], [78.2925, 17.15145]
    ]
    legacy_geom_p107 = {"type": "Polygon", "coordinates": [legacy_coords_p107]}
    leg_props_107 = compute_metric_properties(legacy_geom_p107)
    disp_107 = compute_boundary_displacement(legacy_geom_p107, p107.geometry)

    disc_107 = BoundaryChange(
        survey_id=survey.id,
        parcel_id=p107.id,
        legacy_cadastral_id="LEG-KOT-107",
        old_geometry=legacy_geom_p107,
        new_geometry=p107.geometry,
        difference_area=round(abs(p107.area - leg_props_107["area_sqm"]), 2),
        difference_acres=round(abs(p107.area_acres - leg_props_107["area_acres"]), 4),
        difference_percentage=round((abs(p107.area_acres - leg_props_107["area_acres"]) / max(leg_props_107["area_acres"], 0.001)) * 100, 2),
        difference_distance=disp_107,
        overlap_ratio=0.94,
        discrepancy_type="Road Margin Variation (1.8m shift)",
        status=DiscrepancyStatus.REQUIRES_REVIEW.value,
        notes="Screening Result: Northern boundary receded 1.8m during village road asphalt extension in 2024."
    )
    db.add(disc_107)

    # 4. Add Cadastral Features (Buildings, Roads, Water Bodies, Trees)
    features_data = [
        # Buildings in P-104 (Village Abadi)
        ("building", {"type": "Polygon", "coordinates": [[[78.2940, 17.1532], [78.2945, 17.1532], [78.2945, 17.1528], [78.2940, 17.1528], [78.2940, 17.1532]]]}, 0.95, p103.id),
        ("building", {"type": "Polygon", "coordinates": [[[78.2946, 17.1531], [78.2950, 17.1531], [78.2950, 17.1527], [78.2946, 17.1527], [78.2946, 17.1531]]]}, 0.93, p103.id),
        ("building", {"type": "Polygon", "coordinates": [[[78.2941, 17.1524], [78.2947, 17.1524], [78.2947, 17.1519], [78.2941, 17.1519], [78.2941, 17.1524]]]}, 0.91, p103.id),
        # Farmhouse in P-101 (Building inside agricultural parcel!)
        ("building", {"type": "Polygon", "coordinates": [[[78.2915, 17.1548], [78.2921, 17.1548], [78.2921, 17.1544], [78.2915, 17.1544], [78.2915, 17.1548]]]}, 0.92, saved_parcels[0][0].id),
        # Village Road Segment
        ("road", {"type": "LineString", "coordinates": [[78.2905, 17.1537], [78.2936, 17.1537], [78.2970, 17.1523]]}, 0.97, None),
        ("road", {"type": "LineString", "coordinates": [[78.2936, 17.1558], [78.2936, 17.1495]]}, 0.96, None),
        # Village Pond in P-106
        ("water_body", {"type": "Polygon", "coordinates": [[[78.2956, 17.1521], [78.2966, 17.1521], [78.2966, 17.1516], [78.2956, 17.1516], [78.2956, 17.1521]]]}, 0.99, saved_parcels[5][0].id),
        # Boundary Wall / Hedge
        ("boundary_wall", {"type": "LineString", "coordinates": [[78.2910, 17.1555], [78.2935, 17.1555]]}, 0.89, saved_parcels[0][0].id),
    ]

    for f_type, f_geom, f_conf, f_pid in features_data:
        feat = CadastralFeature(
            survey_id=survey.id,
            parcel_id=f_pid,
            feature_type=f_type,
            geometry=f_geom,
            confidence=f_conf,
            properties={"category": f_type.replace("_", " ").title(), "source": "AI Inference (YOLO / Spectral)"}
        )
        db.add(feat)

    # 5. Verification History for verified parcel P-101
    v_hist = VerificationHistory(
        parcel_id=saved_parcels[0][0].id,
        action="VERIFY",
        old_geometry=saved_parcels[0][0].geometry,
        new_geometry=saved_parcels[0][0].geometry,
        user_id=1,
        user_name="K. Rajeshwar Rao, Dy. Inspector",
        reason="Ground verification completed with DGPS Survey Pillar GPS-KOT-12. Boundaries conform strictly to Revenue Register."
    )
    db.add(v_hist)

    # 6. Change Detection Run (Survey 2025 vs Survey 2026)
    cd_run = ChangeDetectionRun(
        survey_a_id=1,
        survey_b_id=1,
        survey_a_name="Ramnagar Baseline Survey 2025",
        survey_b_name="Ramnagar Drone Survey 2026",
        new_buildings_count=3,
        removed_structures_count=1,
        boundary_changes_count=4,
        landuse_changes_count=2,
        change_summary={
            "new_buildings": ["B-01 (Agro-shed in P-101)", "B-04 (Residential extension in P-104)", "B-05 (Grain storage)"],
            "removed_structures": ["Old thatch granary in P-102"],
            "boundary_changes": ["P-103 eastern field bund shifted 2.4m", "P-107 road edge widened 1.8m"],
            "landuse_changes": ["P-105 converted from agricultural to agro-commercial"]
        },
        change_geojson={
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [78.2918, 17.1546]},
                    "properties": {"change_type": "new_building", "description": "New farm structure constructed in late 2025"}
                },
                {
                    "type": "Feature",
                    "geometry": {"type": "LineString", "coordinates": [[78.2933, 17.1536], [78.2935, 17.1536]]},
                    "properties": {"change_type": "boundary_shift", "description": "Field bund shifted 2.4m east"}
                }
            ]
        }
    )
    db.add(cd_run)

    db.commit()
    return survey
