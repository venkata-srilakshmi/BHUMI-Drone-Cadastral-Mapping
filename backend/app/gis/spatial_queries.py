import re
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from shapely.geometry import shape
from shapely.ops import transform
from app.models.models import Parcel, CadastralFeature, BoundaryChange
from app.gis.geometry_utils import to_metric_polygon

def interpret_and_execute_spatial_query(
    query_text: str,
    survey_id: int,
    db: Session
) -> Dict[str, Any]:
    """
    Interprets natural language GIS queries securely using predefined intent matching
    and executes Shapely / SQLAlchemy spatial queries.
    """
    q = query_text.lower().strip()
    matched_parcel_ids = []
    matched_feature_ids = []
    intent = "unknown"
    summary = ""

    # Fetch all parcels and features for this survey
    parcels = db.query(Parcel).filter(Parcel.survey_id == survey_id).all()
    features = db.query(CadastralFeature).filter(CadastralFeature.survey_id == survey_id).all()
    discrepancies = db.query(BoundaryChange).filter(BoundaryChange.survey_id == survey_id).all()

    # Intent 1: Buildings inside agricultural parcels
    if ("building" in q or "structure" in q) and ("agri" in q or "farm" in q or "crop" in q):
        intent = "buildings_in_agricultural_parcels"
        agri_parcels = [p for p in parcels if "agri" in p.land_use.lower()]
        building_features = [f for f in features if f.feature_type == "building"]

        for b in building_features:
            b_poly = shape(b.geometry)
            for p in agri_parcels:
                p_poly = shape(p.geometry)
                if p_poly.intersects(b_poly):
                    matched_parcel_ids.append(p.parcel_id)
                    matched_feature_ids.append(b.id)

        matched_parcel_ids = list(set(matched_parcel_ids))
        summary = (
            f"Found {len(matched_feature_ids)} building(s) sited within "
            f"{len(matched_parcel_ids)} agricultural land parcel(s)."
        )

    # Intent 2: Boundary discrepancies / changes / encroachment
    elif "discrepan" in q or "encroach" in q or "shift" in q or "conflict" in q or "differ" in q:
        intent = "parcels_with_discrepancies"
        for d in discrepancies:
            if d.difference_distance >= 1.0 or d.difference_percentage >= 3.0:
                p = next((x for x in parcels if x.id == d.parcel_id), None)
                if p:
                    matched_parcel_ids.append(p.parcel_id)
        
        summary = (
            f"Identified {len(matched_parcel_ids)} parcel(s) with boundary discrepancies "
            f"exceeding survey screening thresholds (> 1.0m shift or > 3% area delta)."
        )

    # Intent 3: Low-confidence parcels
    elif "low-confidence" in q or "low confidence" in q or "confidence" in q:
        intent = "low_confidence_parcels"
        for p in parcels:
            if p.confidence < 0.85:
                matched_parcel_ids.append(p.parcel_id)
        
        summary = (
            f"Found {len(matched_parcel_ids)} parcel(s) with AI confidence below 85% "
            f"requiring mandatory ground inspection."
        )

    # Intent 4: Verification status / Requires verification
    elif "verif" in q or "pending" in q or "review" in q:
        intent = "pending_verification_parcels"
        for p in parcels:
            if p.status in ["pending_review", "flagged_discrepancy"]:
                matched_parcel_ids.append(p.parcel_id)
        
        summary = (
            f"Found {len(matched_parcel_ids)} parcel(s) currently awaiting human officer "
            f"verification or boundary adjudication."
        )

    # Intent 5: Near roads / pathway accessibility
    elif "road" in q or "path" in q or "access" in q:
        intent = "parcels_near_roads"
        road_features = [f for f in features if f.feature_type in ["road", "pathway"]]
        for r in road_features:
            r_geom = shape(r.geometry)
            for p in parcels:
                p_geom = shape(p.geometry)
                # Compute distance in metric projection
                m_r = to_metric_polygon(r_geom)
                m_p = to_metric_polygon(p_geom)
                if m_p.distance(m_r) <= 15.0: # within 15 meters
                    matched_parcel_ids.append(p.parcel_id)
                    matched_feature_ids.append(r.id)

        matched_parcel_ids = list(set(matched_parcel_ids))
        summary = (
            f"Identified {len(matched_parcel_ids)} parcel(s) within 15 meters of village road networks."
        )

    # Intent 6: Water bodies
    elif "water" in q or "pond" in q or "canal" in q:
        intent = "water_body_parcels"
        water_features = [f for f in features if f.feature_type == "water_body"]
        for w in water_features:
            matched_feature_ids.append(w.id)
            w_geom = shape(w.geometry)
            for p in parcels:
                p_geom = shape(p.geometry)
                if p_geom.intersects(w_geom):
                    matched_parcel_ids.append(p.parcel_id)

        matched_parcel_ids = list(set(matched_parcel_ids))
        summary = (
            f"Identified {len(matched_parcel_ids)} parcel(s) intersecting natural drainage or water bodies."
        )

    # Fallback
    else:
        intent = "all_parcels_query"
        matched_parcel_ids = [p.parcel_id for p in parcels[:5]]
        summary = (
            f"Showing top {len(matched_parcel_ids)} parcels for general query: '{query_text}'. "
            f"Try asking: 'Show buildings inside agricultural parcels' or 'Show parcels with boundary discrepancies'."
        )

    return {
        "query": query_text,
        "interpreted_intent": intent,
        "matched_parcel_ids": matched_parcel_ids,
        "matched_feature_ids": matched_feature_ids,
        "summary_message": summary,
        "count": len(matched_parcel_ids)
    }
