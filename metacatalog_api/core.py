import os
from pathlib import Path

from metacatalog import api
from models import Metadata, from_entry
from dotenv import load_dotenv
from pydantic_geojson import FeatureCollectionModel


load_dotenv()

METACATALOG_URI = os.getenv("METACATALOG_URI", 'postgresql://metacatalog:metacatalog@localhost:5432/metacatalog')
SQL_DIR = Path(__file__).parent / "sql"

# helper function to load sql files
def load_sql(file_name: str) -> str:
    path = Path(file_name)
    if not path.exists():
        path = SQL_DIR / file_name
    
    with open(path, 'r') as f:
        return f.read()
        

def entries(offset: int = 0, limit: int = 100, filter: dict = {}) -> list[Metadata]:
    # get a database session
    session = api.connect_database(METACATALOG_URI)

    # get the sql for the query
    sql = api.find_entry(session, return_iterator=True, **filter).offset(offset).limit(limit)

    # execute the query
    results = [from_entry(entry) for entry in sql]

    # close the session and return the results
    session.close()

    return results

def entries_locations(filter: dict = {}) -> FeatureCollectionModel:
    # get a database session
    session = api.connect_database(METACATALOG_URI)

    # build the filter
    filt = ""
    if len(filter.keys()) > 0:
        filt = " AND " + "  AND ".join([f"{k} = '{v}'" for k, v in filter.items()])
    
    # load the query
    sql = load_sql("entries_locations.sql").format(filter=filt)

    # execute the query
    result = session.execute(sql).one() 

    # close the session and return the results
    session.close()

    return result["json_build_object"]


