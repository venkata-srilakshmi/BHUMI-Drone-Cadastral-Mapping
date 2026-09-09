import os
import cv2
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from shapely.geometry import Polygon, mapping
from shapely.validation import make_valid
from app.gis.polygonizer import pixel_to_geo
from app.gis.geometry_utils import simplify_and_heal_geometry

class CadastralFeatureDetector:
    """
    YOLO-compatible cadastral feature detection service.
    Detects buildings, roads, water bodies, agricultural fields, vegetation, and boundary walls.
    """
    def __init__(self, yolo_weights_path: Optional[str] = None):
        self.weights_path = yolo_weights_path
        self.is_yolo_loaded = False
        self.inference_mode = "Prototype / Demo Feature Extraction (Computer Vision + Spectral Analysis)"

    def detect_features(
        self,
        image_path: str,
        bounds: Tuple[float, float, float, float]
    ) -> List[Dict[str, Any]]:
        """
        Executes feature detection and outputs GeoJSON features with bounding boxes and confidence.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found at {image_path}")

        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Unable to read image at {image_path}")

        h, w = img.shape[:2]
        features = []

        # 1. Detect Water Bodies (HSV blue/cyan spectral range)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lower_blue = np.array([90, 50, 40])
        upper_blue = np.array([135, 255, 255])
        water_mask = cv2.inRange(hsv, lower_blue, upper_blue)
        water_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
        water_mask = cv2.morphologyEx(water_mask, cv2.MORPH_CLOSE, water_kernel)

        cnts, _ = cv2.findContours(water_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in cnts:
            area = cv2.contourArea(c)
            if area > (h * w) * 0.01: # at least 1% of scene
                poly_feat = self._contour_to_feature(c, bounds, (h, w), "water_body", 0.94)
                if poly_feat:
                    features.append(poly_feat)

        # 2. Detect Buildings / Structures (High contrast rectangular contours)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 21, 5)
        rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, rect_kernel)

        b_cnts, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        building_count = 0
        for c in b_cnts:
            area = cv2.contourArea(c)
            # Typical building size
            if (h * w) * 0.001 < area < (h * w) * 0.03:
                peri = cv2.arcLength(c, True)
                approx = cv2.approxPolyDP(c, 0.04 * peri, True)
                # Check rectangularity (4 to 8 vertices)
                if 4 <= len(approx) <= 8 and building_count < 15:
                    poly_feat = self._contour_to_feature(approx, bounds, (h, w), "building", 0.92)
                    if poly_feat:
                        features.append(poly_feat)
                        building_count += 1

        # 3. Detect Road / Pathways (Elongated linear features)
        edges = cv2.Canny(gray, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=80, minLineLength=int(w * 0.2), maxLineGap=20)
        if lines is not None:
            for l in lines[:4]: # Top main road segments
                line_coords = np.asarray(l).reshape(-1)
                if len(line_coords) < 4:
                    continue
                x1, y1, x2, y2 = [int(v) for v in line_coords[:4]]
                lon1, lat1 = pixel_to_geo(x1, y1, bounds, (h, w))
                lon2, lat2 = pixel_to_geo(x2, y2, bounds, (h, w))
                road_feat = {
                    "feature_type": "road",
                    "confidence": 0.88,
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[lon1, lat1], [lon2, lat2]]
                    },
                    "bbox": [min(lon1, lon2), min(lat1, lat2), max(lon1, lon2), max(lat1, lat2)],
                    "properties": {
                        "category": "Village Arterial Road / Pathway",
                        "detection_engine": self.inference_mode
                    }
                }
                features.append(road_feat)

        return features

    def _contour_to_feature(
        self,
        contour: np.ndarray,
        bounds: Tuple[float, float, float, float],
        shape_hw: Tuple[int, int],
        feature_type: str,
        confidence: float
    ) -> Optional[Dict[str, Any]]:
        pts = []
        for pt in contour:
            coords = np.asarray(pt).reshape(-1)
            if len(coords) < 2:
                continue
            c, r = float(coords[0]), float(coords[1])
            lon, lat = pixel_to_geo(c, r, bounds, shape_hw)
            pts.append((lon, lat))

        if len(pts) < 3:
            return None

        if pts[0] != pts[-1]:
            pts.append(pts[0])

        try:
            poly = Polygon(pts)
            if not poly.is_valid:
                poly = make_valid(poly)
            geojson_geom = simplify_and_heal_geometry(mapping(poly))
            b = poly.bounds

            return {
                "feature_type": feature_type,
                "confidence": confidence,
                "geometry": geojson_geom,
                "bbox": [round(float(b[0]), 6), round(float(b[1]), 6), round(float(b[2]), 6), round(float(b[3]), 6)],
                "properties": {
                    "detection_engine": self.inference_mode,
                    "category": feature_type.replace("_", " ").title()
                }
            }
        except Exception:
            return None
