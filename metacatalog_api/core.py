from typing import List
import os
from pathlib import Path
from contextlib import contextmanager

import psycopg
import psycopg.rows
from metacatalog_api import models
from dotenv import load_dotenv
from pydantic_geojson import FeatureCollectionModel

from metacatalog_api import db


load_dotenv()

METACATALOG_URI = os.environ.get("METACATALOG_URI", 'postgresql://metacatalog:metacatalog@localhost:5432/metacatalog')
SQL_DIR = Path(__file__).parent / "sql"

#METACATALOG_URI="postgresql://postgres:postgres@localhost:5433/metacatalog"
print(METACATALOG_URI)

@contextmanager
def connect(autocommit: bool = True):
    with psycopg.connect(METACATALOG_URI, autocommit=autocommit) as con:
        with con.cursor(row_factory=psycopg.rows.dict_row) as cur:
            yield cur


def entries(offset: int = 0, limit: int = 100, ids: int | List[int] = None,  search: str = None, filter: dict = {}) -> list[models.Metadata]:
    # check if we filter or search
    with connect() as session:
        if search is not None:
            search_results = db.search_entries(session, search, limit=limit, offset=offset)

            if len(search_results) == 0:
                return []
            # in any other case get them by id
            # in any other case, request the entries by id
            results = db.get_entries_by_id(session=session, entry_ids=[r["id"] for r in search_results])

            return results
        elif ids is not None:
            results = db.get_entries_by_id(session, ids, limit=limit, offset=offset)
        else:
            results = db.get_entries(session, limit=limit, offset=offset, filter=filter)

    return results


def entries_locations(ids: int | List[int] = None, limit: int = None, offset: int = None, search: str = None, filter: dict = {}) -> FeatureCollectionModel:
    # handle the ids
    if ids is None:
        ids = []
    if isinstance(ids, int):
        ids = [ids]
    
    # check if we filter or search
    with connect() as session:
        # run the search to ge the ids
        if search is not None:
            search_results = db.search_entries(session, search, limit=limit, offset=offset)
            ids = [*ids, *[r["id"] for r in search_results]]
        
            # if no ids have been found, return an empty FeatureCollection
            if len(ids) == 0:
                return {"type": "FeatureCollection", "features": []}
        
        # in any other case we go for the locations.
        result = db.get_entries_locations(session, ids=ids, limit=limit, offset=offset)
    
    return result


def licenses(id: int = None, offset: int = None, limit: int = None):
    with connect() as session:
        if id is not None:
            result = db.get_license_by_id(session, id=id)
        else:
            result = db.get_licenses(session, limit=limit, offset=offset)
    
    return result


def authors(id: int = None, entry_id: int = None, search: str = None, exclude_ids: List[int] = None, offset: int = None, limit: int = None) -> List[models.Author]:
    with connect() as session:
        # if an author_id is given, we return only the author of that id
        if id is not None:
            authors = db.get_author_by_id(session, id=id)
        # if an entry_id is given, we return only the authors of that entry
        elif entry_id is not None:
            authors = db.get_authors_by_entry(session, entry_id=entry_id)
        else:
            authors = db.get_authors(session, search=search, exclude_ids=exclude_ids, limit=limit, offset=offset)
    
    return authors


def variables(id: int = None, only_available: bool = False, offset: int = None, limit: int = None) -> List[models.Variable]:
    with connect() as session:
        if only_available:
            variables = db.get_available_variables(session, limit=limit, offset=offset)
        elif id is not None:
            variables = [db.get_variable_by_id(session, id=id)]
        else:
            variables = db.get_variables(session, limit=limit, offset=offset)
    
    return variables

def datatypes(id: int = None) -> List[models.DataSourceType]:
    # TODO: this may need some more parameters
    with connect() as session:
        return db.get_datatypes(session, id=id)


def add_entry(payload: models.MetadataPayload) -> models.Metadata:
    # get the variable
    # TODO: put this into the server, as this is due to the FORM. the core package should use the payload model
    # if 'variable_id' in flat_dict or 'variable.id' in flat_dict:
    #     vid = flat_dict.pop('variable_id', flat_dict.pop('variable.id'))
    #     variable = variables(id=vid)[0]
    
    # # overload the payload with the variable from the database
    # flat_dict['variable'] = variable.model_dump()

    # load the payload model
    #payload = utils.metadata_payload_to_model(flat_dict)

    # add the entry to the database
    with connect() as session:
        metadata = db.add_entry(session, payload=payload)

        # check if there is a datasource in the payload
        if 'datasource' in payload:
            datasource_id = db.add_datasource(session, entry_id=metadata.id, datasource=payload['datasource'])
            metadata.datasource_id = datasource_id
    
    return metadata


def add_datasource(entry_id: int, payload: models.DataSource) -> models.DataSource:
    with connect() as session:
        datasource_id = db.add_datasource(session, entry_id=entry_id, datasource=payload)
        
    return datasource_id