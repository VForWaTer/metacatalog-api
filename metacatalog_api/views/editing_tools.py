"""
This module contains extra views that are only helpful if running the HTML version
of Metacatalog API. These views are rendered as a FastAPI blueprint and can be loaded
by any main template to make editing easier for the user.
"""
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

# initialize the router
edit_router = APIRouter()

# initialize the templates
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


@edit_router.get("/leaflet_draw.html")
def leaflet_draw(request: Request, geom: str = 'marker'):
    if geom.lower() == 'marker':
        return templates.TemplateResponse(request=request, name="leaflet_marker.html", context={})
    elif geom.lower() == 'extent':
        return templates.TemplateResponse(request=request, name="leaflet_extent.html", context={})