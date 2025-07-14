from pathlib import Path

from fastapi import APIRouter, Request, HTTPException
from fastapi.templating import Jinja2Templates

from metacatalog_api.core import core
from metacatalog_api.server import server

export_router = APIRouter()

templates = Jinja2Templates(directory=Path(__file__).parent / 'templates')


@export_router.get('/entries/{id}.xml')
def get_entry_xml(id: int, request: Request):
    # call the function
    entries = core.entries(ids=id)
    groups = core.groups(entry_id=id)

    
    if len(entries) == 0:
        raise HTTPException(status_code=404, detail=f"Entry of <ID={id}> not found")
    
    return templates.TemplateResponse(request=request, name="entry.xml", context={"entry": entries[0], "groups": groups, "path": server.app_prefix}, media_type='application/xml')
