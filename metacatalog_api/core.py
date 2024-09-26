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
def connect():
    with psycopg.connect(METACATALOG_URI, autocommit=True) as con:
        with con.cursor(row_factory=psycopg.rows.dict_row) as cur:
            yield cur

# helper function to load sql files
def load_sql(file_name: str) -> str:
    path = Path(file_name)
    if not path.exists():
        path = SQL_DIR / file_name
    
    with open(path, 'r') as f:
        return f.read()
        

def entries(offset: int = 0, limit: int = 100, ids: int | List[int] = None,  search: str = None, filter: dict = {}) -> list[Metadata]:
    # check if we filter or search
    with connect() as session:
        if search is not None:
            results = db.search_entries(session, search, limit=limit, offset=offset)
        elif ids is not None:
            results = db.get_entries_by_id(session, ids, limit=limit, offset=offset)
        else:
            results = db.get_entries(session, limit=limit, offset=offset, filter=filter)

    return results


def entries_locations(filter: dict = {}) -> FeatureCollectionModel:
    # build the filter
    filt = ""
    if len(filter.keys()) > 0:
        filt = " AND " + "  AND ".join([f"{k} = '{v}'" for k, v in filter.items()])
    
    # load the query
    sql = load_sql("entries_locations.sql").format(filter=filt)

    # execute the query
    with connect() as session:
        result = session.execute(sql).fetchone() 

    return result["json_build_object"]


