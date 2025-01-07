from fastapi import APIRouter

from metacatalog_api import core
from metacatalog_api import models

create_router = APIRouter()

@create_router.post('/entries')
def add_entry(payload: models.EntryCreate, author_duplicates: bool = False) -> models.Metadata:
    metadata = core.add_entry(payload, author_duplicates=author_duplicates)
    return metadata


@create_router.post('/entries/{entry_id}/datasource')
def add_datasource(entry_id: int, payload: models.DatasourceCreate) -> models.Metadata:
    metadata = core.add_datasource(entry_id=entry_id, payload=payload)
    return metadata

@create_router.post('/authors')
def add_author(payload: models.AuthorCreate, no_duplicates: bool = True) -> models.Author:
    """
    Create a new Author. If the author already exists, the existing author is returned.
    If no_duplicates is set to False, the author will be dupliacted with different UUID.
    """
    author = core.add_author(payload, no_duplicates=no_duplicates)
    return author

@create_router.post('/groups')
def add_group(payload: models.EntryGroupCreate) -> models.EntryGroup:
    group = core.add_group(payload=payload)
    return group
