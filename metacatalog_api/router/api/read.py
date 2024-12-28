from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from pydantic_geojson import FeatureCollectionModel

from metacatalog_api import core
read_router = APIRouter()


@read_router.get('/entries')
@read_router.get('/entries.json')
def get_entries(offset: int = 0, limit: int = 100, search: str = None, full_text: bool = True, title: str = None, description: str = None, variable: str = None):

    # sanitize the search
    if search is not None and search.strip() == '':
        search = None

    # call the function
    entries = core.entries(offset, limit, search=search, full_text=full_text, title=title, variable=variable) 

    return entries

@read_router.get('/locations.json', response_model=FeatureCollectionModel)
def get_entries_geojson(search: str = None, offset: int = None, limit: int = None, ids: int | list[int] = None):   
    # in all other casese call the function and return the feature collection
    geometries = core.entries_locations(limit=limit, offset=offset, search=search, ids=ids)
    
    return geometries

@read_router.get('/entries/{id}')
@read_router.get('/entries/{id}.json')
def get_entry(id: int):
    # call the function
    entries = core.entries(ids=id)
    
    if len(entries) == 0:
        raise HTTPException(status_code=404, detail=f"Entry of <ID={id}> not found")
    return entries[0]

@read_router.get('/licenses')
@read_router.get('/licenses.json')
def get_licenses(license_id: int | None = None):
    # call the function
    try:
        licenses = core.licenses(id=license_id)
    except Exception as e:
         raise HTTPException(status_code=404, detail=str(e))

    return licenses


@read_router.get('/authors')
@read_router.get('/authors.json')
@read_router.get('/entries/{entry_id}/authors')
@read_router.get('/entries/{entry_id}/authors.json')
def get_authors(entry_id: int | None = None, author_id: int | None = None, search: str = None, exclude_ids: list[int] = None, target: str = None, offset: int = None, limit: int = None):
    try:
        authors = core.authors(id=author_id, entry_id=entry_id, search=search, exclude_ids=exclude_ids, offset=offset, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

    return authors
@read_router.get('/authors/{author_id}')
@read_router.get('/authors/{author_id}.json')
def get_author(author_id: int):
    try:
        author = core.authors(id=author_id)
        return author
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@read_router.get('/variables')
@read_router.get('/variables.json')
def get_variables(offset: int = None, limit: int = None):
    try:
        variables = core.variables(only_available=False, offset=offset, limit=limit)
    except Exception as e:
        return HTTPException(status_code=404, detail=str(e))

    return variables
