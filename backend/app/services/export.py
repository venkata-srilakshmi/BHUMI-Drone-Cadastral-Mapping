import io
import csv
import json
from typing import List
from app.models.models import Parcel, Survey

def export_parcels_geojson(parcels: List[Parcel], survey: Survey) -> dict:
    """Generates standard GeoJSON FeatureCollection preserving all properties and WGS84 coordinates."""
    features = []
    for p in parcels:
        discrepancy_info = {}
        if p.discrepancy:
            discrepancy_info = {
                "boundary_displacement_m": p.discrepancy.difference_distance,
                "area_diff_acres": p.discrepancy.difference_acres,
                "area_diff_percentage": p.discrepancy.difference_percentage,
                "discrepancy_status": p.discrepancy.status
            }

        feat = {
            "type": "Feature",
            "id": p.parcel_id,
            "geometry": p.geometry,
            "properties": {
                "parcel_id": p.parcel_id,
                "survey_id": p.survey_id,
                "village": survey.village,
                "mandal": survey.mandal,
                "district": survey.district,
                "state": survey.state,
                "area_acres": p.area_acres,
                "area_sqm": p.area,
                "perimeter_m": p.perimeter,
                "centroid_lat": p.centroid_lat,
                "centroid_lon": p.centroid_lon,
                "confidence": p.confidence,
                "status": p.status,
                "land_use": p.land_use,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
                **discrepancy_info
            }
        }
        features.append(feat)

    return {
        "type": "FeatureCollection",
        "name": f"BHOOMI_AI_{survey.name.replace(' ', '_')}",
        "crs": {
            "type": "name",
            "properties": {
                "name": "urn:ogc:def:crs:OGC:1.3:CRS84"
            }
        },
        "features": features
    }

def export_parcels_csv(parcels: List[Parcel], survey: Survey) -> str:
    """Generates CSV format string representing revenue parcel register."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    headers = [
        "Parcel ID", "Survey Name", "Village", "Mandal", "District", "State",
        "Area (Acres)", "Area (Sq.m)", "Perimeter (m)", "Centroid Lat", "Centroid Lon",
        "AI Confidence (%)", "Status", "Land Use", "Boundary Displacement (m)", "Discrepancy Status"
    ]
    writer.writerow(headers)

    for p in parcels:
        displacement = p.discrepancy.difference_distance if p.discrepancy else 0.0
        disc_status = p.discrepancy.status if p.discrepancy else "Conforming"
        writer.writerow([
            p.parcel_id,
            survey.name,
            survey.village,
            survey.mandal,
            survey.district,
            survey.state,
            p.area_acres,
            p.area,
            p.perimeter,
            p.centroid_lat,
            p.centroid_lon,
            round(p.confidence * 100, 1),
            p.status.upper(),
            p.land_use,
            displacement,
            disc_status
        ])

    return output.getvalue()

def export_parcels_kml(parcels: List[Parcel], survey: Survey) -> str:
    """Generates OGC KML 2.2 XML file for Google Earth and GNSS handheld terminals."""
    kml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<kml xmlns="http://www.opengis.net/kml/2.2">',
        '  <Document>',
        f'    <name>{survey.name} - BHOOMI-AI Parcels</name>',
        f'    <description>Cadastral parcel mapping for {survey.village}, {survey.mandal}</description>',
        '    <Style id="verifiedParcel">',
        '      <LineStyle><color>ff00aa00</color><width>2</width></LineStyle>',
        '      <PolyStyle><color>4000ff00</color></PolyStyle>',
        '    </Style>',
        '    <Style id="pendingParcel">',
        '      <LineStyle><color>ff00aaff</color><width>2</width></LineStyle>',
        '      <PolyStyle><color>4000ffff</color></PolyStyle>',
        '    </Style>',
        '    <Style id="discrepancyParcel">',
        '      <LineStyle><color>ff0000ff</color><width>2.5</width></LineStyle>',
        '      <PolyStyle><color>400000ff</color></PolyStyle>',
        '    </Style>'
    ]

    for p in parcels:
        style = "pendingParcel"
        if p.status == "verified":
            style = "verifiedParcel"
        elif p.discrepancy and p.discrepancy.difference_distance > 1.2:
            style = "discrepancyParcel"

        geom = p.geometry
        coords_str = ""
        if geom.get("type") == "Polygon":
            exterior = geom.get("coordinates", [[]])[0]
            coords_str = " ".join([f"{pt[0]},{pt[1]},0" for pt in exterior])

        kml.append('    <Placemark>')
        kml.append(f'      <name>{p.parcel_id}</name>')
        kml.append(f'      <styleUrl>#{style}</styleUrl>')
        kml.append('      <description><![CDATA[')
        kml.append(f'<b>Parcel ID:</b> {p.parcel_id}<br/>')
        kml.append(f'<b>Area:</b> {p.area_acres} acres ({p.area} sqm)<br/>')
        kml.append(f'<b>Confidence:</b> {round(p.confidence*100,1)}%<br/>')
        kml.append(f'<b>Status:</b> {p.status}<br/>')
        kml.append(f'<b>Land Use:</b> {p.land_use}<br/>')
        kml.append('      ]]></description>')
        if coords_str:
            kml.append('      <Polygon>')
            kml.append('        <outerBoundaryIs><LinearRing>')
            kml.append(f'          <coordinates>{coords_str}</coordinates>')
            kml.append('        </LinearRing></outerBoundaryIs>')
            kml.append('      </Polygon>')
        kml.append('    </Placemark>')

    kml.append('  </Document>')
    kml.append('</kml>')
    return "\n".join(kml)
