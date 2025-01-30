try:
    import osmnx as ox
    OSMNX_LOADED = True
except ImportError:
    OSMNX_LOADED = False
from functools import cache

from pydantic_geojson import PolygonModel
from shapely import wkt
from shapely import from_geojson



BBOX = tuple[float, float, float, float]

CIRCLE = tuple[tuple[float, float], float]

#@cache
def geolocation_to_postgres_wkt(geolocation: str | PolygonModel | BBOX | CIRCLE, tolerance: float = None) -> str:
    """
    Transforms a number of GeoLocation inputs to a Polygon WKT
    """
    if isinstance(geolocation, (tuple, list)):
        if len(geolocation) == 4:
            le, lo, ri, up = geolocation
            return f"SRID=4326;POLYGON (({le} {lo}, {le} {up}, {ri} {up}, {ri} {lo}, {le} {lo}))"
        elif len(geolocation) == 2:
            raise NotImplementedError
        else:
            raise ValueError(f"If geolocation is a tuple, you can only pass a BBox (left, lower, right, upper) or a Cirlce ((center x, center y) radius). Got {geolocation}.")
    elif isinstance(geolocation, PolygonModel):
        return f"SRID=4326;{wkt.dumps(from_geojson(geolocation.model_dump_json()))}"
    
    # From here on, geolocation is a string and might either be a geocode or a valid WKT
    if 'polygon' in geolocation:
        shape = wkt.loads(geolocation)
        if not shape.is_valid:
            raise ValueError(f"The shape {shape} is not valid")
        return f"SRID=4326;{wkt.dumps(shape)}"
    
    else:
        if not OSMNX_LOADED:
            raise RuntimeError(f"Seems like the geolocation {geolocation} needs to be geocoded, but OSMnx is not installed. Please install using `pip install osmnx`")
        wkt = wkt_from_geocode(geolocation, tolerance=tolerance)
        if wkt is None:
            raise ValueError(f"The string {geolocation} is neither a valid WKT containing a Polygon Geometry, nor is it a Address or Place that could successfully be geocoded.")
        return f"SRID=4326;{wkt}"


def wkt_from_geocode(location: str, tolerance: float = None) -> str | None:
    if not OSMNX_LOADED:
        raise RuntimeError(f"Seems like the geolocation {location} needs to be geocoded, but OSMnx is not installed. Please install using `pip install osmnx`")
    
    try:
        result = ox.geocode_to_gdf(location)
    except TypeError:
        # no result was found
        return None
    
    if tolerance is None:
        return str(result.loc[0, 'geometry'])
    else:
        return str(result.loc[0, 'geometry'].simplify(tolerance))
