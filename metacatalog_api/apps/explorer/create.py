from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from metacatalog_api import core
from metacatalog_api.server import server

create_router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).parent / 'templates')

@create_router.get('/entries/new.html')
def new_entry_page(request: Request):
    return templates.TemplateResponse(request=request, name="add_entry.html", context={"path": server.uri_prefix})


@create_router.get("/utils/leaflet_draw.html")
def leaflet_draw(request: Request, geom: str = 'marker'):
    if geom.lower() == 'marker':
        return templates.TemplateResponse(request=request, name="leaflet_marker.html", context={})
    elif geom.lower() == 'extent':
        return templates.TemplateResponse(request=request, name="leaflet_extent.html", context={})


@create_router.get('/authors/new.html')
def new_author(request: Request):
    return templates.TemplateResponse(request=request, name="author.html", context={"path": server.uri_prefix})


@create_router.get('/details/new.html')
def new_details(request: Request):
    return templates.TemplateResponse(request=request, name="details.html", context={"path": server.uri_prefix})


@create_router.get('/datasources/new.html')
def new_datasource(request: Request):
    # load the datasource types
    types = core.datatypes()
    return templates.TemplateResponse(request=request, name="add_datasource.html", context={"types": types, "path": server.uri_prefix})
