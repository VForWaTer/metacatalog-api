from typing import Literal, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.templating import Jinja2Templates
from pydantic_geojson import FeatureCollectionModel

import core

# define the format literal
FMT = Optional[Literal['html', 'json']]


# build the base app
app = FastAPI()

# add the templates
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


@app.get('/')
def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})


@app.get('/entries')
@app.get('/entries.{fmt}')
def get_entries(request: Request, fmt: FMT = None, offset: int = 0, limit: int = 100, search: str = None, title: str = None, description: str = None, variable: str = None):
    """
    Load all entries from the database. 
    You may add a filter, limit and offset.
    """
    # build the filter
    filter = {'entries.title': title, 'entries.abstract': description, 'variables.name': variable}

    # call the function
    entries = core.entries(offset, limit, search=search,  filter={k: v for k, v in filter.items() if v is not None}) 
    
    # check if we should return html
    if fmt == 'html':
        return templates.TemplateResponse(request=request, name="entries.html", context={"entries": entries})
    return entries


@app.get('/entries/{id}')
@app.get('/entries/{id}.{fmt}')
def get_entry(id: int, request: Request, fmt: FMT = None):
    # call the function
    entries = core.entries(ids=id)
    
    if len(entries) == 0:
        return HTTPException(status_code=404, detail=f"Entry of <ID={id}> not found")
    
    # check if we should return html
    if fmt == 'html':
        return templates.TemplateResponse(request=request, name="entry.html", context={"entry": entries[0]})
    return entries[0]


@app.get('/locations.{fmt}', response_model=FeatureCollectionModel)
def get_entries_geojson(request: Request, fmt: FMT = None):
    # check if we should return html
    if fmt == 'html':
        return templates.TemplateResponse(request=request, name="map.html", context={})
    
    # in all other casese call the function and return the feature collection
    geometries = core.entries_locations()
    
    return geometries


if __name__ == "__main__":
    import uvicorn
    uvicorn.run('server:app', host="0.0.0.0", port=8000, reload=True)
