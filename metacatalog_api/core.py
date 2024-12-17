from typing import List, Generator
import os
from pathlib import Path
from contextlib import contextmanager

from sqlmodel import Session, create_engine, text
from metacatalog_api import models
from dotenv import load_dotenv
from pydantic_geojson import FeatureCollectionModel

from metacatalog_api import db
#from metacatalog_api import __version__ as metacatalog_version


load_dotenv()

METACATALOG_URI = os.environ.get("METACATALOG_URI", 'postgresql://metacatalog:metacatalog@localhost:5432/metacatalog')
SQL_DIR = Path(__file__).parent / "sql"


@contextmanager
def connect(url: str = None) -> Generator[Session, None, None]:
    uri = url if url is not None else METACATALOG_URI
    engine = create_engine(uri)

    with Session(engine) as session:
        yield session

def get_session(url: str = None) -> Session:
    if url is None:
        url = os.getenv('METACATALOG_URI')
        
    engine = create_engine(url)
    return Session(engine)


def migrate_db(schema: str = 'public') -> None:
    # get the current version
    with connect() as session:
        current_version = db.get_db_version(session, schema=schema)['db_version']
    
    # as long as the local _DB_VERSION is higher than the remote version, we can load a migration
    if current_version < db.DB_VERSION:
        # get the migration sql
        migration_sql = db.load_sql(SQL_DIR / 'migrate' / f'migration_{current_version + 1}.sql').format(schema=schema)
        
        # run
        with connect() as session:
            session.exec(text(migration_sql))
            
            # update the db version
            session.exec(text(f"INSERT INTO {schema}.metacatalog_info (db_version) VALUES ({current_version + 1});")) 
            session.commit()
        # inform the user
        print(f"Migrated database from version {current_version} to {current_version + 1}")
        
        # finally call the migration function recursively
        migrate_db()
        

def entries(offset: int = 0, limit: int = None, ids: int | List[int] = None, full_text: bool = True, search: str = None, variable: str | int = None, title: str = None) -> list[models.Metadata]:
    # check if we filter or search
    with connect() as session:
        if search is not None:
            search_results = db.search_entries(session, search, limit=limit, offset=offset, variable=variable, full_text=full_text)

            if len(search_results) == 0:
                return []
            # in any other case get them by id
            # in any other case, request the entries by id
            results = db.get_entries_by_id(session=session, entry_ids=[r.id for r in search_results])

            return results
        elif ids is not None:
            results = db.get_entries_by_id(session, ids, limit=limit, offset=offset)
        else:
            results = db.get_entries(session, limit=limit, offset=offset, variable=variable, title=title)

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
            ids = [*ids, *[r.id for r in search_results]]
        
            # if no ids have been found, return an empty FeatureCollection
            if len(ids) == 0:
                return {"type": "FeatureCollection", "features": []}
        
        # in any other case we go for the locations.
        result = db.get_entries_locations(session, ids=ids, limit=limit, offset=offset)
    
    return result


def licenses(id: int = None, offset: int = None, limit: int = None) -> models.License | list[models.License]:
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


def datatypes(id: int = None) -> List[models.DatasourceTypeBase]:
    # TODO: this may need some more parameters
    with connect() as session:
        return db.get_datatypes(session, id=id)


def add_entry(payload: models.EntryCreate) -> models.Metadata:
    # add the entry
    with connect() as session:
        entry = db.add_entry(session, payload=payload)
    
        # check if there was a datasource
        if payload.datasource is not None:
            entry = db.add_datasource(session, entry_id=entry.id, datasource=payload.datasource)
        session.commit()
    return entry

def add_datasource(entry_id: int, payload: models.DatasourceCreate) -> models.Metadata:
    with connect() as session:
        entry = db.add_datasource(session, entry_id=entry_id, datasource=payload)

    return entry