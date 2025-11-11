from typing import List, Generator, Dict, Any, Callable, Optional
import os
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime
import mimetypes

from sqlmodel import Session, create_engine, text
from metacatalog_api import models
from dotenv import load_dotenv
from pydantic_geojson import FeatureCollectionModel

from metacatalog_api import db
from metacatalog_api.file_uploads import UploadCache
from metacatalog_api import access_control


load_dotenv()

METACATALOG_URI = os.environ.get("METACATALOG_URI", 'postgresql://metacatalog:metacatalog@localhost:5432/metacatalog')
SQL_DIR = Path(__file__).parent / "sql"

cache = UploadCache()


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


def register_token(user: models.Author | None = None, valid_until: datetime | None = None):
    with connect() as session:
        new_key = access_control.register_new_token(session, user, valid_until)

    print(f"Generated a new token. Save this token in a save space as it will not be displayed again:\n{new_key}\n")


def entries(offset: int = 0, limit: int = None, ids: int | List[int] = None, full_text: bool = True, search: str = None, variable: str | int = None, title: str = None, geolocation: str = None) -> list[models.Metadata]:
    # check if we filter or search
    with connect() as session:
        if search is not None:
            search_results = db.search_entries(session, search, limit=limit, offset=offset, variable=variable, full_text=full_text, geolocation=geolocation)

            if len(search_results) == 0:
                return []
            # in any other case get them by id
            # in any other case, request the entries by id
            results = db.get_entries_by_id(session=session, entry_ids=[r.id for r in search_results])

            return results
        elif ids is not None:
            results = db.get_entries_by_id(session, ids, limit=limit, offset=offset)
        else:
            results = db.get_entries(session, limit=limit, offset=offset, variable=variable, title=title, geolocation=geolocation)

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


def groups(id: int = None, title: str = None, description: str = None, type: str = None, entry_id: int = None, with_metadata: bool = False, limit: int = None, offset: int = None):
    with connect() as session:
        if id is not None or (title is not None and '%' not in title):
            group = db.get_group(session, id=id, title=title, with_metadata=with_metadata)
            return group
        else:
            groups = db.get_groups(session, title=title, description=description, type=type, entry_id=entry_id, limit=limit, offset=offset)
            return groups 


def group_types():
    with connect() as session:
        return db.get_grouptypes(session)


def licenses(id: int = None, offset: int = None, limit: int = None) -> models.License | list[models.License]:
    with connect() as session:
        if id is not None:
            result = db.get_license_by_id(session, id=id)
        else:
            result = db.get_licenses(session, limit=limit, offset=offset)
    
    return result


def authors(id: int = None, entry_id: int = None, search: str = None, name: str = None, exclude_ids: List[int] = None, offset: int = None, limit: int = None) -> List[models.Author]:
    with connect() as session:
        # if an author_id is given, we return only the author of that id
        if id is not None:
            authors = db.get_author_by_id(session, id=id)
        # if an entry_id is given, we return only the authors of that entry
        elif entry_id is not None:
            authors = db.get_authors_by_entry(session, entry_id=entry_id)
        elif name is not None:
            authors = db.get_authors_by_name(session, name=name, limit=limit, offset=offset)
        else:
            authors = db.get_authors(session, search=search, exclude_ids=exclude_ids, limit=limit, offset=offset)
    
    return authors


def author(id: int = None, name: str = None, search: str = None) -> models.Author | None:
    with connect() as session:
        if id is not None:
            author = db.get_author_by_id(session, id=id)
        elif name is not None:
            author = db.get_author_by_name(session, name=name)
        else:
            authors = db.get_authors(session, search=search, limit=1) 
            if len(authors) == 0:
                author = None
            else:
                author = authors[0]
    return author


def variables(id: int = None, only_available: bool = False, offset: int = None, limit: int = None) -> List[models.Variable]:
    with connect() as session:
        if only_available:
            variables = db.get_available_variables(session, limit=limit, offset=offset)
        elif id is not None:
            variables = db.get_variable_by_id(session, id=id)
        else:
            variables = db.get_variables(session, limit=limit, offset=offset)
    
    return variables


def keywords(id: int = None, search: str = None, thesaurus_id: int = None, offset: int = None, limit: int = None) -> List[models.Keyword]:
    with connect() as session:
        if id is not None:
            keyword = db.get_keyword_by_id(session, id=id)
            return keyword
        else:
            keywords = db.get_keywords(session, search=search, thesaurus_id=thesaurus_id, limit=limit, offset=offset)
            return keywords


def datatypes(id: int = None) -> List[models.DatasourceTypeBase]:
    # TODO: this may need some more parameters
    with connect() as session:
        return db.get_datatypes(session, id=id)


def add_author(payload: models.AuthorCreate, no_duplicates: bool = True) -> models.Author:
    with connect() as session:
        if no_duplicates:
            author = db.create_or_get_author(session, payload)
        else:
            author = db.add_author(session, payload)
    
    return author


def add_entry(payload: models.EntryCreate, author_duplicates: bool = False) -> models.Metadata:
    # add the entry
    with connect() as session:
        entry = db.add_entry(session, payload=payload, author_duplicates=author_duplicates)
    
        # check if there was a datasource
        if payload.datasource is not None:
            # if the path is in the UploadCache, the file was already uploaded and just needs to be copied
            if payload.datasource.path in cache:
                new_path = cache.save_to_data(file_hash=payload.datasource.path)
                payload.datasource.path = str(new_path)

            entry = db.add_datasource(session, entry_id=entry.id, datasource=payload.datasource)
        session.commit()

        # handle groups
        if payload.groups is not None and len(payload.groups) > 0:
            for group in payload.groups:
                db.group_entries(session=session, group=group, entry_ids=[entry.id])
    return entry


def add_datasource(entry_id: int, payload: models.DatasourceCreate) -> models.Metadata:
    # if the path is in the UploadCache, the file was already uploaded and just needs to be copied
    if payload.path in cache:
        new_path = cache.save_to_data(file_hash=payload.path)
        payload.path = str(new_path)

    with connect() as session:
        entry = db.add_datasource(session, entry_id=entry_id, datasource=payload)

    return entry


def add_group(payload: models.EntryGroupCreate) -> models.EntryGroup:
    with connect() as session:
        group = db.add_group(
            session=session,
            title=payload.title,
            description=payload.description, 
            type=payload.type,
            entry_ids=payload.entry_ids
        )
    return group


def get_entry_data_file(entry_id: int) -> Dict[str, Any]:
    """
    Get data file information for an entry.
    
    Returns:
        dict with keys:
        - file_path: Path object or None
        - mime_type: str or None
        - filename: str or None
        - stream_generator: callable generator or None
        - is_stream: bool
        - error: str or None
    """
    # Get entry
    entry_list = entries(ids=entry_id)
    if len(entry_list) == 0:
        return {
            'file_path': None,
            'mime_type': None,
            'filename': None,
            'stream_generator': None,
            'is_stream': False,
            'error': f"Metadata Entry of id <ID={entry_id}> not found"
        }
    
    entry = entry_list[0]
    datasource = entry.datasource
    if datasource is None:
        return {
            'file_path': None,
            'mime_type': None,
            'filename': None,
            'stream_generator': None,
            'is_stream': False,
            'error': f"Metadata Entry of id <ID={entry_id}> has no datasource"
        }
    
    # Check for unsupported cases
    if '*' in datasource.path:
        return {
            'file_path': None,
            'mime_type': None,
            'filename': None,
            'stream_generator': None,
            'is_stream': False,
            'error': "MetaCatalog API does currently not support streaming of wildcard paths"
        }
    
    if Path(datasource.path).is_dir():
        return {
            'file_path': None,
            'mime_type': None,
            'filename': None,
            'stream_generator': None,
            'is_stream': False,
            'error': f"Metadata Entry of id <ID={entry_id}> points to a directory. GZip result streaming is not yet supported."
        }
    
    # Handle different datasource types
    if datasource.type.name == "internal":
        # Internal table - return generator function
        def stream_internal_table():
            headers = []
            if datasource.temporal_scale is not None:
                headers.extend(datasource.temporal_scale.dimension_names)
            if datasource.spatial_scale is not None:
                headers.extend(datasource.spatial_scale.dimension_names)
            headers.extend(datasource.variable_names)
            yield ",".join(headers) + "\n"
            sql = text(f"SELECT * FROM {datasource.path};")
            with connect() as session:
                for record in session.exec(sql):
                    yield ",".join([str(c) for c in record]) + "\n"
        
        return {
            'file_path': None,
            'mime_type': 'text/csv',
            'filename': f'entry_{entry_id}_data.csv',
            'stream_generator': stream_internal_table,
            'is_stream': True,
            'error': None
        }
    
    elif datasource.type.name == "external":
        return {
            'file_path': None,
            'mime_type': None,
            'filename': None,
            'stream_generator': None,
            'is_stream': False,
            'error': f"Metadata Entry of id <ID={entry_id}> is external and cannot be downloaded"
        }
    
    elif datasource.type.name in ["csv", "local", "netCDF"]:
        # Resolve file path (handle hash-based paths from upload cache)
        file_path = None
        if datasource.path in cache:
            # Path is a hash, get actual file from cache
            file_info = cache.get_file(datasource.path)
            file_path = file_info.file
            original_filename = file_info.filename
        else:
            # Path is a regular file path
            file_path = Path(datasource.path)
            original_filename = file_path.name
        
        if not file_path.exists() or not file_path.is_file():
            return {
                'file_path': None,
                'mime_type': None,
                'filename': None,
                'stream_generator': None,
                'is_stream': False,
                'error': f"Data file not found at path: {datasource.path}"
            }
        
        # Determine MIME type and filename
        if datasource.type.name == "csv":
            mime_type = "text/csv"
            filename = original_filename if datasource.path in cache else "data.csv"
        elif datasource.type.name == "netCDF":
            mime_type = "application/netcdf"
            filename = original_filename if datasource.path in cache else "data.nc"
        else:  # local
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if mime_type is None:
                mime_type = "application/octet-stream"
            filename = original_filename
        
        return {
            'file_path': file_path,
            'mime_type': mime_type,
            'filename': filename,
            'stream_generator': None,
            'is_stream': False,
            'error': None
        }
    
    else:
        return {
            'file_path': None,
            'mime_type': None,
            'filename': None,
            'stream_generator': None,
            'is_stream': False,
            'error': f"Metadata Entry of id <ID={entry_id}> has an unknown datasource type: {datasource.type.name if datasource.type else 'unknown'}"
        }
