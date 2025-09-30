from pathlib import Path

from fastapi import APIRouter, Request, HTTPException
from fastapi.templating import Jinja2Templates

from metacatalog_api import core
from metacatalog_api.server import server

export_router = APIRouter()

templates = Jinja2Templates(directory=Path(__file__).parent / 'templates')


@export_router.get('/export/{entry_id}/json')
def export_json(entry_id: int):
    """
    MetaCatalog JSON
    Export entry as JSON format
    """
    entries = core.entries(ids=entry_id)
    
    if len(entries) == 0:
        raise HTTPException(status_code=404, detail=f"Entry of <ID={entry_id}> not found")
    
    return entries[0]


@export_router.get('/export/{entry_id}/xml')
def export_xml(entry_id: int, request: Request):
    """
    MetaCatalog XML
    Export entry as XML format using Jinja template
    """
    entries = core.entries(ids=entry_id)
    groups = core.groups(entry_id=entry_id)
    
    if len(entries) == 0:
        raise HTTPException(status_code=404, detail=f"Entry of <ID={entry_id}> not found")
    
    return templates.TemplateResponse(
        request=request, 
        name="entry.xml", 
        context={"entry": entries[0], "groups": groups, "path": server.app_prefix}, 
        media_type='application/xml'
    )


@export_router.get('/export/{entry_id}/dublincore')
def export_dublincore(entry_id: int, request: Request):
    """
    Dublin Core
    Export entry as Dublin Core XML format using Jinja template
    """
    entries = core.entries(ids=entry_id)
    
    if len(entries) == 0:
        raise HTTPException(status_code=404, detail=f"Entry of <ID={entry_id}> not found")
    
    return templates.TemplateResponse(
        request=request, 
        name="dublincore.xml", 
        context={"entry": entries[0]}, 
        media_type='application/xml'
    )


@export_router.get('/export/{entry_id}/schemaorg')
def export_schemaorg(entry_id: int, request: Request):
    """
    Schema.org Dataset
    Export entry as Schema.org Dataset JSON-LD format using Jinja template
    """
    entries = core.entries(ids=entry_id)
    
    if len(entries) == 0:
        raise HTTPException(status_code=404, detail=f"Entry of <ID={entry_id}> not found")
    
    return templates.TemplateResponse(
        request=request, 
        name="schemaorg.json", 
        context={"entry": entries[0]}, 
        media_type='application/ld+json'
    )


@export_router.get('/export/{entry_id}/rdf')
def export_rdf(entry_id: int, request: Request):
    """
    RDF/XML
    Export entry as RDF/XML format using hybrid vocabulary approach
    """
    entries = core.entries(ids=entry_id)
    
    if len(entries) == 0:
        raise HTTPException(status_code=404, detail=f"Entry of <ID={entry_id}> not found")
    
    return templates.TemplateResponse(
        request=request, 
        name="rdf.xml", 
        context={"entry": entries[0]}, 
        media_type='application/xml'
    )


@export_router.get('/export/{entry_id}/datacite')
def export_datacite(entry_id: int, request: Request):
    """
    DataCite
    Export entry as DataCite XML format for research repositories like Zenodo
    """
    entries = core.entries(ids=entry_id)
    
    if len(entries) == 0:
        raise HTTPException(status_code=404, detail=f"Entry of <ID={entry_id}> not found")
    
    return templates.TemplateResponse(
        request=request, 
        name="datacite.xml", 
        context={"entry": entries[0]}, 
        media_type='application/xml'
    )
