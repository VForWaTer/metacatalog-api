from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import HTTPException
from fastapi.templating import Jinja2Templates

from metacatalog_api import core
from metacatalog_api.server import server

explorer_router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).parent / 'templates')

# add static files
explorer_router.mount("/static", StaticFiles(directory=Path(__file__).parent / "templates" / "static"), name="static")


@explorer_router.get('/entries.html')
def get_entries_page(request: Request, offset: int = 0, limit: int = 100, search: str = None, full_text: bool = True, title: str = None, description: str = None, variable: str = None):

    # sanitize the search
    if search is not None and search.strip() == '':
        search = None

    # call the function
    entries = core.entries(offset, limit, search=search, full_text=full_text, title=title, variable=variable) 
    
    # check if we should return html
    return templates.TemplateResponse(request=request, name="entries.html", context={"entries": entries, "path": server.uri_prefix})


@explorer_router.get('/locations.html')
def get_entries_geojson_page(request: Request):
    # check if we should return html
    return templates.TemplateResponse(request=request, name="map.html", context={"path": server.uri_prefix})


@explorer_router.get('/entries/{id}.html')
def get_entry_page(id: int, request: Request):
    # call the function
    entries = core.entries(ids=id)
    
    if len(entries) == 0:
        raise HTTPException(status_code=404, detail=f"Entry of <ID={id}> not found")
    
    # check if we should return html
    return templates.TemplateResponse(request=request, name="entry.html", context={"entry": entries[0], "path": server.uri_prefix})
    

@explorer_router.get('/entries/{id}.xml')
@explorer_router.get('/entries/{id}.radar.xml')
def get_entry_radar_xml(id: int, request: Request):
    # call the function
    entries = core.entries(ids=id)
    
    if len(entries) == 0:
        raise HTTPException(status_code=404, detail=f"Entry of <ID={id}> not found")
    
    return templates.TemplateResponse(request=request, name="entry.radar.xml", context={"entry": entries[0], "path": server.uri_prefix}, media_type='application/xml')


@explorer_router.get('/licenses.html')
def get_licenses_page(request: Request,  license_id: int | None = None):
    # call the function
    try:
        licenses = core.licenses(id=license_id)
    except Exception as e:
         raise HTTPException(status_code=404, detail=str(e))

    # check the number if a id was given
    if license_id is not None:
        return templates.TemplateResponse(request=request, name="license.html", context={"license": licenses.model_dump()})
    else:
        return templates.TemplateResponse(request=request, name="licenses.html", context={"licenses": licenses, "path": server.uri_prefix})


@explorer_router.get('/authors.html')
@explorer_router.get('/entries/{entry_id}/authors.html')
def get_authors_page(request: Request, entry_id: int | None = None, author_id: int | None = None, search: str = None, exclude_ids: list[int] = None, target: str = None, offset: int = None, limit: int = None):
    try:
        authors = core.authors(id=author_id, entry_id=entry_id, search=search, exclude_ids=exclude_ids, offset=offset, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

    # check if an author_id is given
    if author_id is not None:
        return templates.TemplateResponse(
            request=request,
            name="author.html",
            context={"author": authors, 'variant': 'fixed', 'target': target, "path": server.uri_prefix}
        )
    
    return templates.TemplateResponse(
        request=request, 
        name="authors.html", 
        context={"authors": authors, 'variant': 'select' if entry_id is None else 'list', 'target': target, "path": server.uri_prefix}
    )

@explorer_router.get('/variables')
@explorer_router.get('/variables.html')
def get_variables_page(request: Request, offset: int = None, limit: int = None):
    try:
        variables = core.variables(only_available=False, offset=offset, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    return templates.TemplateResponse(
        request=request, 
        name="variables.html", 
        context={"variables": variables, "path": server.uri_prefix}
    )
