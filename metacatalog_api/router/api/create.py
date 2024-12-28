from fastapi import APIRouter

from metacatalog_api import core
from metacatalog_api import models

create_router = APIRouter()

@create_router.post('/entries')
def add_entry(payload: models.EntryCreate) -> models.Metadata:
    metadata = core.add_entry(payload)
    return metadata


@create_router.post('/entries/{entry_id}/datasource')
def add_datasource(entry_id: int, payload: models.DatasourceCreate) -> models.Metadata:
    metadata = core.add_datasource(entry_id=entry_id, payload=payload)
    return metadata
