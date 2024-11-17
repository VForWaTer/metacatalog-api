from typing import Literal, Optional, List
from pathlib import Path
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic_geojson import FeatureCollectionModel

from metacatalog_api import core
from metacatalog_api.views import editing_tools
from metacatalog_api import  utils

logger = logging.getLogger('uvicorn.error')

# before we initialize the app, we check that the database is installed and up to date
@asynccontextmanager
async def lifespan(app: FastAPI):
    # check if the entries table can be found in the database
    with core.connect() as session:
        if not core.db.check_installed(session):
            logger.info("Database not installed, installing...")
            core.db.install(session, populate_defaults=True)
            logger.info("Database installed.")

    # now we yield the application
    yield

    # here we can app tear down code - i.e. a log message

# define the format literal
FMT = Optional[Literal['html', 'json']]


# build the base app
app = FastAPI(lifespan=lifespan)

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

    # sanitize the search
    if search is not None and search.strip() == '':
        search = None

    # call the function
    entries = core.entries(offset, limit, search=search,  filter={k: v for k, v in filter.items() if v is not None}) 
    
    # check if we should return html
    if fmt == 'html':
        return templates.TemplateResponse(request=request, name="entries.html", context={"entries": entries})
    return entries


@app.get('/entries/new.html')
def new_entry_page(request: Request):
    return templates.TemplateResponse(request=request, name="add_entry.html", context={})


@app.post('/entries')
async def insert_entry(request: Request):
    # collect form data an convert it to a dict
    form = await request.form()
    data = dict(form)

    # check if there is a variable id to be loaded
    if 'variable_id' in data or 'variable.id' in data:
        vid = data.pop('variable_id', data.pop('variable.id'))
        variable = core.variables(id=vid)[0]

        # append the variable to the data
        data['variable'] = variable.model_dump()

    # second: turn the form data into a metadata payload
    payload = utils.metadata_payload_to_model(data)

    # check if the payload contained a datasource
    if 'datasource' in payload:
        datasource = utils.datasource_payload_to_model(payload['datasource'])
        payload['datasource'] = datasource
    
    # add the entry and return the response
    entry = core.add_entry(payload)
    
    return HTMLResponse(f'<pre><code>{entry}</code></pre>')

@app.get('/entries/{id}')
@app.get('/entries/{id}.{fmt}')
def get_entry(id: int, request: Request, fmt: Literal['xml'] | FMT = None):
    # call the function
    entries = core.entries(ids=id)
    
    if len(entries) == 0:
        return HTTPException(status_code=404, detail=f"Entry of <ID={id}> not found")
    
    # check if we should return html
    if fmt == 'html':
        return templates.TemplateResponse(request=request, name="entry.html", context={"entry": entries[0]})
    elif fmt == 'xml':
        return templates.TemplateResponse(request=request, name="entry.xml", context={"entry": entries[0]}, media_type='application/xml')
    return entries[0]


@app.get('/locations.{fmt}', response_model=FeatureCollectionModel)
def get_entries_geojson(request: Request, fmt: FMT = None, search: str = None, offset: int = None, limit: int = None, ids: int | List[int] = None):
    # check if we should return html
    if fmt == 'html':
        return templates.TemplateResponse(request=request, name="map.html", context={})
    
    # in all other casese call the function and return the feature collection
    geometries = core.entries_locations(limit=limit, offset=offset, search=search, ids=ids)
    
    return geometries


@app.get('/licenses.{fmt}')
def get_licenses(request: Request, fmt: FMT, license_id: Optional[int] = None, variant: Literal['list', 'select'] = 'select'):
    # call the function
    try:
        licenses = core.licenses(id=license_id)
    except Exception as e:
        return HTTPException(status_code=404, detail=str(e))

    # check if we should return html
    if fmt == 'html':
        # check the number if a id was given
        if license_id is not None:
            return templates.TemplateResponse(request=request, name="license.html", context={"license": licenses.model_dump()})
        else:
            return templates.TemplateResponse(request=request, name="licenses.html", context={"licenses": licenses, "variant": variant})
    else:
        return licenses


@app.get('/authors/new.html')
def new_author(request: Request):
    return templates.TemplateResponse(request=request, name="author.html", context={})

@app.get('/authors')
@app.get('/authors.{fmt}')
@app.get('/entries/{entry_id}/authors.{fmt}')
def get_authors(request: Request, fmt: FMT = None, entry_id: int = None, author_id: int = None, search: str = None, exclude_ids: List[int] = None, target: str = None, offset: int = None, limit: int = None):
    try:
        authors = core.authors(id=author_id, entry_id=entry_id, search=search, exclude_ids=exclude_ids, offset=offset, limit=limit)
    except Exception as e:
        return HTTPException(status_code=404, detail=str(e))

    if fmt == 'html':
        if author_id is not None:
            return templates.TemplateResponse(
                request=request,
                name="author.html",
                context={"author": authors, 'variant': 'fixed', 'target': target}
            )
        return templates.TemplateResponse(
            request=request, 
            name="authors.html", 
            context={"authors": authors, 'variant': 'select' if entry_id is None else 'list', 'target': target}
        )
    else:
        return [author.model_dump() for author in authors]


@app.get('/authors/{author_id}')
@app.get('/authors/{author_id}.json')
def get_author(author_id: int, request: Request):
    try:
        author = core.authors(id=author_id)
        return author
    except Exception as e:
        return HTTPException(status_code=404, detail=str(e))


@app.get('/variables')
@app.get('/variables.{fmt}')
def get_variables(request: Request, fmt: FMT = None, offset: int = None, limit: int = None):
    if fmt == 'html':
        return templates.TemplateResponse(request=request, name="variables.html", context={})
    try:
        variables = core.variables(only_available=False, offset=offset, limit=limit)
    except Exception as e:
        return HTTPException(status_code=404, detail=str(e))
    
    if fmt == 'html':
        return templates.TemplateResponse(
            request=request, 
            name="variables.html", 
            context={"variables": variables}
        )
    else:
        return variables

@app.get('/details/new.html')
def new_details(request: Request):
    return templates.TemplateResponse(request=request, name="details.html", context={})

@app.get('/datasources/new.html')
def new_datasource(request: Request):
    # load the datasource types
    types = core.datatypes()
    return templates.TemplateResponse(request=request, name="add_datasource.html", context={"types": types})

@app.post('/datasources')
async def add_datasource(request: Request):
    # collect form data an convert it to a dict
    form = await request.form()
    data = dict(form)

    # check that the type is provided
    if 'type_id' in data:
        dtype = core.datatypes(id=data['type_id'])[0] 
        data['type'] = dtype.model_dump()

    # turn this into a payload
    payload = utils.datasource_payload_to_model(data)

    # add the datasource and return the response
    datasource = core.add_datasource(-1, payload)

    # add the entry and return the response
    return HTMLResponse(f'<pre><code>{datasource}</code></pre>')

# register the editing tools
app.include_router(editing_tools.edit_router, prefix='/utils')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run('server:app', host="0.0.0.0", port=8000, reload=True)
