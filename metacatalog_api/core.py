from typing import List
import os
from pathlib import Path
from contextlib import contextmanager

import psycopg
import psycopg.rows
from models import Metadata
from dotenv import load_dotenv
from pydantic_geojson import FeatureCollectionModel

import db


load_dotenv()

METACATALOG_URI = os.getenv("METACATALOG_URI", 'postgresql://metacatalog:metacatalog@localhost:5432/metacatalog')
SQL_DIR = Path(__file__).parent / "sql"

@contextmanager
def connect(autocommit: bool = True):
    with psycopg.connect(METACATALOG_URI, autocommit=autocommit) as con:
        with con.cursor(row_factory=psycopg.rows.dict_row) as cur:
            yield cur


def entries(offset: int = 0, limit: int = 100, ids: int | List[int] = None,  search: str = None, filter: dict = {}) -> list[Metadata]:
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