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
    Export entry as JSON format
    """
    entries = core.entries(ids=entry_id)
    
    if len(entries) == 0:
        raise HTTPException(status_code=404, detail=f"Entry of <ID={entry_id}> not found")
    
    return entries[0]


@export_router.get('/export/{entry_id}/xml')
def export_xml(entry_id: int, request: Request):
    """
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
