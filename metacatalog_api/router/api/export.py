from pathlib import Path

import httpx

from fastapi import APIRouter, Request, HTTPException
from fastapi.templating import Jinja2Templates

from metacatalog_api import core
from metacatalog_api.server import server

export_router = APIRouter()

templates = Jinja2Templates(directory=Path(__file__).parent / 'templates')


def render_export(app, entry_id: int, format_name: str, request: Request) -> tuple[str, str]:
    """
    Dynamically render an entry export by making a request to the export API endpoint.
    Uses ASGI transport for efficient internal requests.
    This works with any export route, including third-party ones.
    
    Returns:
        tuple: (content, filename) where content is the rendered export as string
               and filename is the suggested filename for the export
    """
    # Make request to the export endpoint using ASGI transport
    export_url = f"/export/{entry_id}/{format_name}"
    
    try:
        with httpx.Client(transport=httpx.ASGITransport(app=app)) as client:
            response = client.get(export_url)
            
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Export format '{format_name}' not found")
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to export format '{format_name}': {response.text}"
                )
            
            # Get content from response
            content = response.text
            
            # Determine filename based on format
            if format_name == 'json':
                filename = "entry.json"
            elif format_name == 'schemaorg':
                filename = "entry_schemaorg.json"
            elif format_name.endswith('.json'):
                filename = f"entry_{format_name}"
            else:
                filename = f"entry_{format_name}.xml"
            
            return content, filename
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to render export format '{format_name}': {str(e)}")


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


@export_router.get('/export/{entry_id}/zku')
def export_zku(entry_id: int, request: Request):
    """
    ZKU/XML
    Export entry as ZKU/XML format for research repositories like Zenodo
    """
    entries = core.entries(ids=entry_id)
    
    if len(entries) == 0:
        raise HTTPException(status_code=404, detail=f"Entry of <ID={entry_id}> not found")
    
    return templates.TemplateResponse(
        request=request, 
        name="zku.xml", 
        context={"entry": entries[0]}, 
        media_type='application/xml'
    )


@export_router.get('/export/{entry_id}/iso19115')
def export_iso19115(entry_id: int, request: Request):
    """
    ISO 19115
    Export entry as ISO 19115/ISO 19139 XML format for geographic metadata
    """
    entries = core.entries(ids=entry_id)
    
    if len(entries) == 0:
        raise HTTPException(status_code=404, detail=f"Entry of <ID={entry_id}> not found")
    
    return templates.TemplateResponse(
        request=request, 
        name="iso19115.xml", 
        context={"entry": entries[0]}, 
        media_type='application/xml'
    )