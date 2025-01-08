from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from pydantic_geojson import FeatureCollectionModel

from metacatalog_api import core
from metacatalog_api import models
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


@read_router.get('/author')
@read_router.get('/author.json')
def get_author_by_name(id: int = None, name: str = None, search: str = None):
    if id is None and name is None and search is None:
        raise HTTPException(status_code=400, detail="Either id, name or search must be provided")
    author = core.author(id=id, name=name, search=search)

    return author


@read_router.get('/variables')
@read_router.get('/variables.json')
def get_variables(only_available: bool = False, offset: int = None, limit: int = None):
    try:
        variables = core.variables(only_available=only_available, offset=offset, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    return variables

@read_router.get('/variable/{id}')
@read_router.get('/variable/{id}.json')
def get_variable(id: int):
    try:
        variable = core.variables(id=id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
    return variable

@read_router.get('/group-types')
@read_router.get('/group-types.json')
def get_group_types():
    try:
        group_types = core.group_types()
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return group_types


@read_router.get('/groups')
@read_router.get('/groups.json')
def get_groups(title: str = None, description: str = None, type: str = None, limit: int = None, offset: int = None) -> list[models.EntryGroup]:
    try:
        groups = core.groups(title=title, description=description, type=type, with_metadata=False, limit=limit, offset=offset)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    
    return groups


@read_router.get('/entries/{entry_id}/groups')
@read_router.get('/entries/{entry_id}/groups.json')
def get_groups_by_entry(entry_id: int) -> list[models.EntryGroup]:
    try:
        groups = core.groups(entry_id=entry_id, with_metadata=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    return groups


@read_router.get('/groups/{group_id}')
@read_router.get('/groups/{group_id}.json')
def get_group(group_id) -> models.EntryGroupWithMetadata:
    try:
        group = core.groups(id=group_id, with_metadata=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    if group is None:
        raise HTTPException(status_code=404, detail=f"Group of id {group_id} was not found.")

    return group