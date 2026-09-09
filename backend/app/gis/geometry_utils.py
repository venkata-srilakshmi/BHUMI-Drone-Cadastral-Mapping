import math
from typing import Tuple, Dict, Any, List
from shapely.geometry import shape, mapping, Polygon, MultiPolygon
from shapely.validation import make_valid
from shapely.ops import transform

SQM_PER_ACRE = 4046.8564224

def get_meter_scale(lat_deg: float) -> Tuple[float, float]:
    """
    Returns meters per degree of (latitude, longitude) at a given latitude.
    Based on WGS84 ellipsoid approximation.
    """
    lat_rad = math.radians(lat_deg)
    m_per_deg_lat = 111132.92 - 559.82 * math.cos(2 * lat_rad) + 1.175 * math.cos(4 * lat_rad)
    m_per_deg_lon = 111412.84 * math.cos(lat_rad) - 93.5 * math.cos(3 * lat_rad)
    return m_per_deg_lat, m_per_deg_lon

def to_metric_polygon(poly: Polygon) -> Polygon:
    """Project a WGS84 polygon into a local metric coordinate system centered at its centroid."""
    if not poly or poly.is_empty:
        return poly
    centroid = poly.centroid
    m_lat, m_lon = get_meter_scale(centroid.y)
    
    def project_to_meters(x, y, z=None):
        dx = (x - centroid.x) * m_lon
        dy = (y - centroid.y) * m_lat
        return (dx, dy)
        
    return transform(project_to_meters, poly)

def compute_metric_properties(geojson_geom: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes area (m² and acres), perimeter (m), and centroid (lat, lon)
    for a given GeoJSON geometry.
    """
    geom = shape(geojson_geom)
    if not geom.is_valid:
        geom = make_valid(geom)

    # Centroid in WGS84
    centroid = geom.centroid
    centroid_lat = round(float(centroid.y), 6)
    centroid_lon = round(float(centroid.x), 6)

    # Convert to metric for accurate area & perimeter calculation
    metric_geom = to_metric_polygon(geom)
    area_sqm = round(float(metric_geom.area), 2)
    area_acres = round(area_sqm / SQM_PER_ACRE, 4)
    perimeter_m = round(float(metric_geom.length), 2)

    return {
        "area_sqm": area_sqm,
        "area_acres": area_acres,
        "perimeter_m": perimeter_m,
        "centroid_lat": centroid_lat,
        "centroid_lon": centroid_lon
    }

def simplify_and_heal_geometry(geojson_geom: Dict[str, Any], tolerance_deg: float = 0.00002) -> Dict[str, Any]:
    """
    Simplifies vertices to remove sensor noise and heals self-intersections.
    """
    geom = shape(geojson_geom)
    if not geom.is_valid:
        geom = make_valid(geom)
        
    simplified = geom.simplify(tolerance_deg, preserve_topology=True)
    if not simplified.is_valid:
        simplified = make_valid(simplified)
        
    # Always ensure polygon / multipolygon
    if simplified.geom_type in ["Polygon", "MultiPolygon"]:
        return mapping(simplified)
    elif simplified.geom_type == "GeometryCollection":
        # Extract polygon parts
        polys = [p for p in simplified.geoms if p.geom_type in ["Polygon", "MultiPolygon"]]
        if polys:
            return mapping(MultiPolygon(polys) if len(polys) > 1 else polys[0])
            
    return mapping(geom)

def compute_boundary_displacement(geom1_json: Dict[str, Any], geom2_json: Dict[str, Any]) -> float:
    """
    Calculates Hausdorff distance (max displacement between boundaries) in meters.
    """
    try:
        g1 = shape(geom1_json)
        g2 = shape(geom2_json)
        
        m_g1 = to_metric_polygon(g1)
        m_g2 = to_metric_polygon(g2)
        
        # Hausdorff distance on exterior boundaries
        dist = m_g1.boundary.hausdorff_distance(m_g2.boundary)
        return round(float(dist), 2)
    except Exception:
        return 0.0
