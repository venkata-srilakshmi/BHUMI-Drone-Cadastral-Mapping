import cv2
import numpy as np
from typing import List, Dict, Any, Tuple
from shapely.geometry import Polygon, mapping
from shapely.validation import make_valid
from app.gis.geometry_utils import compute_metric_properties, simplify_and_heal_geometry

def pixel_to_geo(
    col: float,
    row: float,
    bounds: Tuple[float, float, float, float], # min_lon, min_lat, max_lon, max_lat
    img_shape: Tuple[int, int]                 # height, width
) -> Tuple[float, float]:
    """
    Transforms pixel (x, y) = (col, row) to geographic coordinates (lon, lat).
    """
    min_lon, min_lat, max_lon, max_lat = bounds
    height, width = img_shape
    
    lon = min_lon + (col / max(width - 1, 1)) * (max_lon - min_lon)
    lat = max_lat - (row / max(height - 1, 1)) * (max_lat - min_lat)
    return round(float(lon), 7), round(float(lat), 7)

def mask_to_parcels(
    binary_mask: np.ndarray,
    bounds: Tuple[float, float, float, float],
    min_area_pixels: int = 500,
    approx_epsilon_factor: float = 0.003
) -> List[Dict[str, Any]]:
    """
    Extracts parcel polygons from a raster segmentation mask, simplifies contours,
    georeferences to EPSG:4326, and calculates GIS properties.
    """
    if binary_mask.dtype != np.uint8:
        binary_mask = (binary_mask > 0).astype(np.uint8) * 255

    # Morphological cleaning: closing small gaps and opening noise
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    cleaned = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)

    # Find contours with hierarchical tree to preserve parcel inner courtyards / exclusions
    contours, hierarchy = cv2.findContours(cleaned, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if not contours or hierarchy is None:
        return []

    hierarchy = hierarchy[0]
    parcels = []
    h, w = binary_mask.shape[:2]

    for idx, cnt in enumerate(contours):
        # Ignore child contours (holes) when finding outer parent boundaries
        parent_idx = hierarchy[idx][3]
        if parent_idx != -1:
            continue

        area_px = cv2.contourArea(cnt)
        if area_px < min_area_pixels:
            continue

        # Douglas-Peucker polygon simplification
        epsilon = approx_epsilon_factor * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)
        if len(approx) < 3:
            continue

        # Extract exterior ring
        exterior_coords = []
        for pt in approx:
            pt_coords = np.asarray(pt).reshape(-1)
            if len(pt_coords) < 2:
                continue
            c, r = float(pt_coords[0]), float(pt_coords[1])
            lon, lat = pixel_to_geo(c, r, bounds, (h, w))
            exterior_coords.append((lon, lat))

        if len(exterior_coords) < 3:
            continue

        # Close loop
        if exterior_coords[0] != exterior_coords[-1]:
            exterior_coords.append(exterior_coords[0])

        # Extract interior rings (holes)
        interior_rings = []
        child_idx = hierarchy[idx][2]
        while child_idx != -1:
            child_cnt = contours[child_idx]
            if cv2.contourArea(child_cnt) >= min_area_pixels * 0.2:
                child_approx = cv2.approxPolyDP(child_cnt, approx_epsilon_factor * cv2.arcLength(child_cnt, True), True)
                if len(child_approx) >= 3:
                    hole_coords = []
                    for pt in child_approx:
                        pt_coords = np.asarray(pt).reshape(-1)
                        if len(pt_coords) < 2:
                            continue
                        c, r = float(pt_coords[0]), float(pt_coords[1])
                        lon, lat = pixel_to_geo(c, r, bounds, (h, w))
                        hole_coords.append((lon, lat))
                    if len(hole_coords) >= 3:
                        if hole_coords[0] != hole_coords[-1]:
                            hole_coords.append(hole_coords[0])
                        interior_rings.append(hole_coords)
            child_idx = hierarchy[child_idx][0]

        try:
            poly = Polygon(exterior_coords, interior_rings)
            if not poly.is_valid:
                poly = make_valid(poly)

            geojson_geom = mapping(poly)
            geojson_geom = simplify_and_heal_geometry(geojson_geom)
            props = compute_metric_properties(geojson_geom)

            parcels.append({
                "geometry": geojson_geom,
                "area_sqm": props["area_sqm"],
                "area_acres": props["area_acres"],
                "perimeter_m": props["perimeter_m"],
                "centroid_lat": props["centroid_lat"],
                "centroid_lon": props["centroid_lon"]
            })
        except Exception:
            continue

    return parcels
