import os
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Tuple, Dict, Any, List, Optional
from PIL import Image
from shapely.geometry import shape, box, Polygon, MultiPolygon
from shapely.ops import unary_union
from shapely.validation import make_valid

VALID_ORTHO_EXTENSIONS = {".tif", ".tiff", ".png", ".jpg", ".jpeg"}
VALID_CADASTRAL_EXTENSIONS = {".geojson", ".json", ".kml", ".shp", ".zip", ".gpkg"}
RASTER_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".gif"}

# Default village prototype bounds (Ramnagar, Telangana: EPSG:4326)
DEFAULT_SURVEY_BOUNDS = (78.2905, 17.1495, 78.2975, 17.1560)

def extract_geotiff_bounds(file_path: Path) -> Optional[Tuple[float, float, float, float]]:
    """
    Attempts to extract geographic bounds (min_lon, min_lat, max_lon, max_lat)
    from a GeoTIFF using rasterio if available, or GeoTIFF tags via Pillow.
    """
    try:
        import rasterio
        with rasterio.open(str(file_path)) as src:
            b = src.bounds
            # If bounds are in valid lon/lat degrees
            if -180 <= b.left <= 180 and -90 <= b.bottom <= 90:
                return (round(float(b.left), 7), round(float(b.bottom), 7),
                        round(float(b.right), 7), round(float(b.top), 7))
            # If bounds are in projected coordinates (e.g. UTM), try reprojecting if pyproj is available
            try:
                from rasterio.warp import transform_bounds
                wgs84_bounds = transform_bounds(src.crs, "EPSG:4326", *src.bounds)
                return (round(float(wgs84_bounds[0]), 7), round(float(wgs84_bounds[1]), 7),
                        round(float(wgs84_bounds[2]), 7), round(float(wgs84_bounds[3]), 7))
            except Exception:
                pass
    except Exception:
        pass

    # Fallback to Pillow TIFF tags
    try:
        with Image.open(str(file_path)) as img:
            tags = img.tag_v2 if hasattr(img, "tag_v2") else {}
            # ModelTiepointTag = 33922, ModelPixelScaleTag = 33550
            if 33922 in tags and 33550 in tags:
                tiepoint = tags[33922]
                scale = tags[33550]
                # tiepoint: (i, j, k, x, y, z) -> pixel (i,j) corresponds to world (x,y)
                # scale: (scale_x, scale_y, scale_z)
                if len(tiepoint) >= 6 and len(scale) >= 2:
                    origin_x = tiepoint[3]
                    origin_y = tiepoint[4]
                    scale_x = scale[0]
                    scale_y = scale[1]
                    w, h = img.size
                    max_x = origin_x + (w * scale_x)
                    min_y = origin_y - (h * scale_y)
                    min_x = origin_x
                    max_y = origin_y
                    if -180 <= min_x <= 180 and -90 <= min_y <= 90:
                        return (round(min_x, 7), round(min_y, 7), round(max_x, 7), round(max_y, 7))
    except Exception:
        pass

    return None

def validate_orthomosaic_file(
    file_path_str: str,
    fallback_bounds: Tuple[float, float, float, float] = DEFAULT_SURVEY_BOUNDS
) -> Dict[str, Any]:
    """
    Validates orthomosaic file existence, format, readability, dimensions, and georeferencing.
    """
    file_path = Path(file_path_str)
    if not file_path.exists():
        raise FileNotFoundError(f"Orthomosaic file not found at: {file_path}")

    file_ext = file_path.suffix.lower()
    if file_ext not in VALID_ORTHO_EXTENSIONS:
        raise ValueError(
            f"Unsupported orthomosaic format '{file_ext}'. "
            f"Supported formats: GeoTIFF (.tif, .tiff), PNG (.png), JPEG (.jpg, .jpeg)."
        )

    if file_path.stat().st_size == 0:
        raise ValueError(f"Uploaded orthomosaic file '{file_path.name}' is empty (0 bytes).")

    # Verify image readability and decode
    try:
        with Image.open(str(file_path)) as img:
            img.verify()
        with Image.open(str(file_path)) as img:
            width, height = img.size
            format_name = img.format
            bands = len(img.getbands()) if hasattr(img, "getbands") else 3
    except Exception as e:
        raise ValueError(f"Corrupted or unreadable image file '{file_path.name}': {str(e)}")

    if width < 10 or height < 10:
        raise ValueError(f"Orthomosaic dimensions ({width}x{height}) are too small for cadastral survey processing.")

    # Determine spatial bounding box & CRS
    bounds = extract_geotiff_bounds(file_path)
    is_georeferenced = bounds is not None
    crs = "EPSG:4326" if is_georeferenced else "Assigned EPSG:4326 (Survey Datum)"

    if not bounds:
        # Check for accompanying ESRI world file (.tfw, .jgw, .pgw, .wld)
        world_exts = {".tif": ".tfw", ".tiff": ".tfw", ".jpg": ".jgw", ".jpeg": ".jgw", ".png": ".pgw"}
        world_file = file_path.with_suffix(world_exts.get(file_ext, ".wld"))
        if world_file.exists():
            try:
                with open(world_file, "r") as wf:
                    lines = [float(line.strip()) for line in wf.readlines() if line.strip()]
                    if len(lines) >= 6:
                        px_size_x, _, _, px_size_y, orig_x, orig_y = lines[:6]
                        min_x = orig_x
                        max_y = orig_y
                        max_x = orig_x + (width * px_size_x)
                        min_y = orig_y + (height * px_size_y)
                        bounds = (min(min_x, max_x), min(min_y, max_y), max(min_x, max_x), max(min_y, max_y))
                        crs = "EPSG:4326 (Worldfile)"
            except Exception:
                pass

    if not bounds:
        bounds = fallback_bounds

    return {
        "filename": file_path.name,
        "format": format_name,
        "width": width,
        "height": height,
        "bands": bands,
        "crs": crs,
        "bounds": bounds,
        "is_georeferenced": is_georeferenced
    }

def _parse_kml(file_path: Path) -> List[Dict[str, Any]]:
    """Extracts polygons and coordinates from a KML file."""
    tree = ET.parse(str(file_path))
    root = tree.getroot()
    ns = {"kml": "http://www.opengis.net/kml/2.2"}
    polygons = []
    
    for poly_elem in root.findall(".//kml:Polygon", ns) or root.findall(".//Polygon"):
        coords_elem = poly_elem.find(".//kml:coordinates", ns) or poly_elem.find(".//coordinates")
        if coords_elem is not None and coords_elem.text:
            raw_pts = coords_elem.text.strip().split()
            pts = []
            for p in raw_pts:
                parts = p.split(",")
                if len(parts) >= 2:
                    try:
                        lon = float(parts[0])
                        lat = float(parts[1])
                        pts.append((lon, lat))
                    except ValueError:
                        continue
            if len(pts) >= 3:
                if pts[0] != pts[-1]:
                    pts.append(pts[0])
                polygons.append({"type": "Polygon", "coordinates": [pts]})
    return polygons

def validate_cadastral_file(file_path_str: str) -> Dict[str, Any]:
    """
    Validates cadastral file format, vector integrity, geometry validity, and spatial extent.
    Explicitly rejects raster image files uploaded into cadastral vector input slots.
    """
    file_path = Path(file_path_str)
    if not file_path.exists():
        raise FileNotFoundError(f"Cadastral vector file not found at: {file_path}")

    file_ext = file_path.suffix.lower()

    # Reject raster images accidentally uploaded as cadastral datasets
    if file_ext in RASTER_EXTENSIONS:
        raise ValueError(
            f"Invalid cadastral dataset format: '{file_path.name}'. "
            f"Raster image files ({file_ext}) cannot be parsed as cadastral vector datasets. "
            f"Please upload a valid vector format: GeoJSON (.geojson, .json), KML (.kml), "
            f"ESRI Shapefile (.zip, .shp), or GeoPackage (.gpkg)."
        )

    if file_ext not in VALID_CADASTRAL_EXTENSIONS:
        raise ValueError(
            f"Unsupported cadastral format '{file_ext}'. "
            f"Supported vector formats: GeoJSON (.geojson, .json), KML (.kml), "
            f"ESRI Shapefile (.zip, .shp), and GeoPackage (.gpkg)."
        )

    if file_path.stat().st_size == 0:
        raise ValueError(f"Uploaded cadastral vector file '{file_path.name}' is empty (0 bytes).")

    geometries = []

    if file_ext in [".geojson", ".json"]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            raise ValueError(f"Malformed JSON in cadastral file '{file_path.name}': {str(e)}")

        if not isinstance(data, dict):
            raise ValueError(f"Invalid GeoJSON structure in '{file_path.name}': root must be a JSON object.")

        geojson_type = data.get("type", "")
        if geojson_type == "FeatureCollection":
            features = data.get("features", [])
            for feat in features:
                geom = feat.get("geometry")
                if geom and geom.get("type") in ["Polygon", "MultiPolygon"]:
                    geometries.append(geom)
        elif geojson_type in ["Polygon", "MultiPolygon", "Feature"]:
            geom = data if geojson_type != "Feature" else data.get("geometry")
            if geom:
                geometries.append(geom)
        else:
            raise ValueError(
                f"Unsupported GeoJSON type '{geojson_type}' in '{file_path.name}'. "
                f"Expected FeatureCollection, Feature, Polygon, or MultiPolygon."
            )

    elif file_ext == ".kml":
        try:
            geometries = _parse_kml(file_path)
        except Exception as e:
            raise ValueError(f"Failed to parse KML cadastral file '{file_path.name}': {str(e)}")

    elif file_ext in [".shp", ".zip", ".gpkg"]:
        try:
            import geopandas as gpd
            gdf = gpd.read_file(str(file_path))
            for g in gdf.geometry:
                if g and not g.is_empty:
                    from shapely.geometry import mapping
                    geometries.append(mapping(g))
        except ImportError:
            raise ValueError(
                f"Processing format '{file_ext}' requires geopandas/pyogrio. "
                f"Please upload standard GeoJSON (.geojson) or KML (.kml) vector datasets."
            )
        except Exception as e:
            raise ValueError(f"Failed to parse vector file '{file_path.name}': {str(e)}")

    if not geometries:
        raise ValueError(
            f"No valid parcel polygons found in cadastral file '{file_path.name}'. "
            f"The file must contain at least one valid Polygon or MultiPolygon geometry."
        )

    # Validate each geometry and compute total spatial extent
    shapely_polys = []
    for g in geometries:
        try:
            poly = shape(g)
            if not poly.is_valid:
                poly = make_valid(poly)
            if not poly.is_empty:
                shapely_polys.append(poly)
        except Exception:
            continue

    if not shapely_polys:
        raise ValueError(f"All geometry features in '{file_path.name}' are topologically invalid or empty.")

    combined = unary_union(shapely_polys)
    min_x, min_y, max_x, max_y = combined.bounds

    # Validate coordinate range (WGS84)
    if not (-180 <= min_x <= 180 and -90 <= min_y <= 90 and -180 <= max_x <= 180 and -90 <= max_y <= 90):
        raise ValueError(
            f"Cadastral coordinates in '{file_path.name}' appear to be in a non-WGS84 projected CRS "
            f"(bounds: [{min_x:.2f}, {min_y:.2f}, {max_x:.2f}, {max_y:.2f}]). "
            f"Please reproject to EPSG:4326 (WGS84 decimal degrees)."
        )

    return {
        "filename": file_path.name,
        "format": file_ext,
        "feature_count": len(shapely_polys),
        "bounds": (round(min_x, 7), round(min_y, 7), round(max_x, 7), round(max_y, 7)),
        "combined_geometry": combined,
        "raw_geometries": geometries
    }

def validate_spatial_overlap(
    ortho_bounds: Tuple[float, float, float, float],
    cadastral_bounds: Tuple[float, float, float, float]
) -> Dict[str, Any]:
    """
    Validates geographic overlap between drone orthomosaic bounds and cadastral vectors.
    Raises a descriptive ValueError if datasets do not overlap.
    """
    ortho_box = box(*ortho_bounds)
    cad_box = box(*cadastral_bounds)

    if not ortho_box.intersects(cad_box):
        raise ValueError(
            "Drone orthomosaic and cadastral dataset do not overlap geographically. "
            f"Please upload datasets for the same survey area. "
            f"(Orthomosaic bounds: [{ortho_bounds[0]:.4f}, {ortho_bounds[1]:.4f}, {ortho_bounds[2]:.4f}, {ortho_bounds[3]:.4f}] vs "
            f"Cadastral bounds: [{cadastral_bounds[0]:.4f}, {cadastral_bounds[1]:.4f}, {cadastral_bounds[2]:.4f}, {cadastral_bounds[3]:.4f}])"
        )

    intersection = ortho_box.intersection(cad_box)
    if intersection.area <= 0:
        raise ValueError(
            "Drone orthomosaic and cadastral dataset do not overlap geographically. "
            "Please upload datasets for the same survey area."
        )

    overlap_pct = min(100.0, round((intersection.area / min(ortho_box.area, cad_box.area)) * 100.0, 1))

    return {
        "overlaps": True,
        "overlap_percentage": overlap_pct,
        "intersection_bounds": intersection.bounds
    }
