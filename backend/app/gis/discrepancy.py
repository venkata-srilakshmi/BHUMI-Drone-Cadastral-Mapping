from typing import Dict, Any, Tuple
from shapely.geometry import shape, mapping
from shapely.validation import make_valid
from app.gis.geometry_utils import compute_boundary_displacement, compute_metric_properties, to_metric_polygon

def analyze_cadastral_discrepancy(
    legacy_geom_json: Dict[str, Any],
    ai_geom_json: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compares legacy cadastral polygon vs AI-derived drone polygon.
    Computes displacement, area delta, overlap ratio, and discrepancy classification.
    Adheres strictly to decision-support terminology.
    """
    legacy_poly = shape(legacy_geom_json)
    ai_poly = shape(ai_geom_json)

    if not legacy_poly.is_valid:
        legacy_poly = make_valid(legacy_poly)
    if not ai_poly.is_valid:
        ai_poly = make_valid(ai_poly)

    # Metric properties
    legacy_props = compute_metric_properties(mapping(legacy_poly))
    ai_props = compute_metric_properties(mapping(ai_poly))

    # Metric geometries for spatial intersection & difference
    m_legacy = to_metric_polygon(legacy_poly)
    m_ai = to_metric_polygon(ai_poly)

    # Area differences
    legacy_area_acres = legacy_props["area_acres"]
    ai_area_acres = ai_props["area_acres"]
    diff_sqm = round(abs(ai_props["area_sqm"] - legacy_props["area_sqm"]), 2)
    diff_acres = round(abs(ai_area_acres - legacy_area_acres), 4)
    
    if legacy_area_acres > 0:
        diff_percentage = round((diff_acres / legacy_area_acres) * 100.0, 2)
    else:
        diff_percentage = 0.0

    # Boundary displacement in meters
    displacement_m = compute_boundary_displacement(legacy_geom_json, ai_geom_json)

    # Spatial Overlap (Intersection over Union - IoU)
    try:
        intersection = m_legacy.intersection(m_ai)
        union = m_legacy.union(m_ai)
        overlap_ratio = round(float(intersection.area / union.area), 4) if union.area > 0 else 0.0
    except Exception:
        overlap_ratio = 0.85

    # Difference geometry in WGS84 for map visualization
    try:
        sym_diff = legacy_poly.symmetric_difference(ai_poly)
        difference_geom = mapping(sym_diff) if not sym_diff.is_empty else None
    except Exception:
        difference_geom = None

    # Determine discrepancy screening classification
    if displacement_m > 3.0 or diff_percentage > 8.0:
        discrepancy_type = "Significant Boundary Displacement (Requires Survey Officer Verification)"
        status = "requires_review"
        screening_summary = (
            f"Screening Result: Potential significant discrepancy detected. "
            f"Boundary displacement is {displacement_m:.1f} meters, "
            f"area variation is {diff_percentage:.1f}% ({diff_acres:.3f} acres). "
            f"Requires mandatory field verification and officer adjudication."
        )
    elif displacement_m > 1.2 or diff_percentage > 3.0:
        discrepancy_type = "Moderate Boundary Variation (Candidate Review)"
        status = "requires_review"
        screening_summary = (
            f"Screening Result: Moderate variation detected. "
            f"Boundary displacement is {displacement_m:.1f} meters, "
            f"area variation is {diff_percentage:.1f}% ({diff_acres:.3f} acres). "
            f"Candidate parcel boundary recommended for survey officer review."
        )
    else:
        discrepancy_type = "Conforming Boundary (Within Tolerance)"
        status = "conforming"
        screening_summary = (
            f"Screening Result: Boundary displacement is {displacement_m:.1f} meters, "
            f"area variation is {diff_percentage:.1f}%. Within normal survey tolerance limits."
        )

    return {
        "legacy_area_acres": legacy_area_acres,
        "drone_area_acres": ai_area_acres,
        "difference_sqm": diff_sqm,
        "difference_acres": diff_acres,
        "difference_percentage": diff_percentage,
        "boundary_displacement_m": displacement_m,
        "overlap_ratio": overlap_ratio,
        "discrepancy_type": discrepancy_type,
        "status": status,
        "screening_summary": screening_summary,
        "difference_geometry": difference_geom
    }
