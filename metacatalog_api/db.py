from typing import List, Dict, Optional
from pathlib import Path
from uuid import uuid4

from models import Author, Metadata, License, Variable
from psycopg import Cursor
from pydantic_geojson import FeatureCollectionModel

SQL_DIR = Path(__file__).parent / "sql"

# helper function to load sql files
def load_sql(file_name: str) -> str:
    path = Path(file_name)
    if not path.exists():
        path = SQL_DIR / file_name
    
    with open(path, 'r') as f:
        return f.read()


def install(cursor: Cursor, schema: str = 'public', populate_defaults: bool = True) -> None:
    # get the install script
    install_sql = load_sql(SQL_DIR / 'maintain' /'install.sql').format(schema=schema)

    # execute the install script
    cursor.execute(install_sql)

    # populate the defaults
    if populate_defaults:
        pupulate_sql = load_sql(SQL_DIR / 'maintain' / 'defaults.sql').replace('{schema}', schema)
        cursor.execute(pupulate_sql)


def check_installed(cursor: Cursor, schema: str = 'public') -> bool:
    try:
        info = cursor.execute(f"SELECT * FROM information_schema.tables WHERE table_schema = '{schema}' AND table_name = 'entries'").fetchone()
        return info is not None
    except Exception:
        return False
    

def get_entries(session: Cursor, limit: int = None, offset: int = None, filter: Dict[str, str] = {}) -> List[Metadata]:
    # build the filter
    if len(filter.keys()) > 0:
        expr = []
        # handle whitespaces
        for col, val in filter.items():
            if '*' in val:
                val = val.replace('*', '%')
            if '%' in val:
                expr.append(f"{col}  LIKE '{val}'")
            else:
                expr.append(f"{col}='{val}'")
        # build the filter
        filt = " WHERE " + " AND ".join(expr)
    else:
        filt = ""
    
    # handle offset and limit
    lim = f" LIMIT {limit} " if limit is not None else ""
    off = f" OFFSET {offset} " if offset is not None else ""

    # get the sql for the query
    sql = load_sql("get_entries.sql").format(filter=filt, limit=lim, offset=off)

    # execute the query
    results = [r for r in session.execute(sql).fetchall()]

    return [Metadata(**result) for result in results]


def get_entries_by_id(session: Cursor, entry_ids: int | List[int], limit: int = None, offset: int = None) -> List[Metadata]:
    if isinstance(entry_ids, int):
        entry_ids = [entry_ids]

    # build the filter
    filt = f"WHERE entries.id IN ({', '.join([str(e) for e in entry_ids])})"

    # handle offset and limit
    lim = f" LIMIT {limit} " if limit is not None else ""
    off = f" OFFSET {offset} " if offset is not None else ""
    
    # get the sql for the query
    sql = load_sql("get_entries.sql").format(filter=filt, limit=lim, offset=off)

    # execute the query
    results = [r for r in session.execute(sql).fetchall()]

    return [Metadata(**result) for result in results]


def get_entries_locations(session: Cursor, ids: List[int] = None, limit: int = None, offset: int = None) -> FeatureCollectionModel:
    # build the id filter
    if ids is None or len(ids) == 0:
        filt = ""
    else:
        filt = f" AND entries.id IN ({', '.join([str(i) for i in ids])})"
    
    # build limit and offset
    lim = f" LIMIT {limit} " if limit is not None else ""
    off = f" OFFSET {offset} " if offset is not None else ""

    # load the query
    sql = load_sql("entries_locations.sql").format(filter=filt, limit=lim, offset=off)

    # execute the query
    result = session.execute(sql).fetchone()['json_build_object']
        
    if result['features'] is None:
        return dict(type="FeatureCollection", features=[])
    
    return result
    

class SearchResult:
    id: int
    matches: List[str]
    weights: int


def search_entries(session: Cursor, search: str, limit: int = None, offset: int = None) -> List[SearchResult]:
    # build the limit and offset
    lim = f" LIMIT {limit} " if limit is not None else ""
    off = f" OFFSET {offset} " if offset is not None else ""

    # get the sql for the query
    sql = load_sql("search_entries.sql").format(prompt=search, limit=lim, offset=off)

    # execute the query
    search_results = [r['search_meta'] for r in session.execute(sql).fetchall()]

    return search_results


def get_authors(session: Cursor, search: str = None, exclude_ids: List[int] = None, limit: int = None, offset: int = None) -> List[Author]:
    # build the filter
    filt = "" if search is None and exclude_ids is None else "WHERE "
    if search is not None:
        filt = f" last_name LIKE {search} OR first_name LIKE {search} OR organisation_name LIKE {search} "
    if exclude_ids is not None:
        if filt != "":
            filt += " AND "
        filt += f" id NOT IN ({', '.join([str(i) for i in exclude_ids])})"
    
    # handle limit and offset
    lim = f" LIMIT {limit} " if limit is not None else ""
    off = f" OFFSET {offset} " if offset is not None else ""
    
    # build the basic query
    sql = "SELECT * FROM persons {filter} {offset} {limit};".format(filter=filt, offset=off, limit=lim)

    # execute the query
    results = session.execute(sql).fetchall()

    return [Author(**result) for result in results]

def get_authors_by_entry(session: Cursor, entry_id: int) -> List[Author]:
    # build the query
    sql = load_sql("get_authors_by_entry.sql").format(entry_id=entry_id)

    # execute the query
    results = session.execute(sql).fetchall()

    return [Author(**result) for result in results]

def get_author_by_id(session: Cursor, id: int) -> Author:
    # build the sql
    sql = "SELECT * FROM persons WHERE id={id};".format(id=id)

    # execute the query
    author = session.execute(sql).fetchone()

    if author is None:
        return None
    else:
        return Author(**author)

def get_variables(session: Cursor, limit: int = None, offset: int = None) -> List[Variable]:
    # build the filter
    filt = ""
    off = f" OFFSET {offset} " if offset is not None else ""
    lim = f" LIMIT {limit} " if limit is not None else ""
    
    # build the basic query
    sql = load_sql('get_variables.sql').format(filter=filt, offset=off, limit=lim)

    # execute the query
    results = session.execute(sql).fetchall()
    
    # build the model
    try:
        variables = [Variable(**result) for result in results]
    except Exception as e:
        print(e)
        raise e
    
    return variables
    

def get_available_variables(session: Cursor, limit: int = None, offset: int = None) -> List[Variable]:
    # build the filter
    filt = ""
    off = f" OFFSET {offset} " if offset is not None else ""
    lim = f" LIMIT {limit} " if limit is not None else ""

    # build the basic query
    sql = load_sql('get_available_variables.sql').format(filter=filt, offset=off, limit=lim)

    # execute the query
    results = session.execute(sql).fetchall()

    return [Variable(**result) for result in results]

def get_licenses(session: Cursor, limit: int = None, offset: int = None) -> List[License]:
    # build the filter
    filt = ""
    off = f" OFFSET {offset} " if offset is not None else ""
    lim = f" LIMIT {limit} " if limit is not None else ""
    
    # build the basic query
    sql = load_sql('get_licenses.sql').format(filter=filt, limit=lim, offset=off)

    # execute the query
    results = session.execute(sql).fetchall()

    return [License(**result) for result in results]

def get_license_by_id(session: Cursor, id: int) -> License:
    # build the filter
    filt = f" WHERE id={id}"

    # build the basic query
    sql = load_sql('get_licenses.sql').format(filter=filt, offset='', limit='')

    # execute the query
    result = session.execute(sql).fetchone()

    if result is None:
        raise ValueError(f"License with id {id} not found")
    else:
        return License(**result)


def get_entry_authors(session: Cursor, entry_id: int) -> List[Author]:
    # build the query
    sql = load_sql("get_entry_authors.sql").format(entry_id=entry_id)

    # execute the query
    results = session.execute(sql).all()

    return [Author(**result) for result in results]


class MetadataPayload(Metadata):
    id: Optional[int] = None
    uuid: Optional[str] = None

def add_entry(session: Cursor, payload: MetadataPayload) -> Metadata:
    # fill out a few fields
    # get the sql for inserting a new entry
    sql = load_sql('insert_entry.sql').format(**payload.model_dump())

    # execute the query
    entry_id = session.execute(sql).fetchone()['id']

    # add the first author
    insert_author = load_sql('insert_author_to_entry.sql')
    
    # add a uuid if there is none
    if payload.author.uuid is None:
        payload.author.uuid = uuid4()
    session.execute(insert_author.format(entry_id=entry_id, role='author', order=1, **payload.author.model_dump()))

    # add co-authors
    if payload.authors is not None and len(payload.authors) > 1:
        for author, idx in enumerate(payload.authors[1:]):
            if author.uuid is None:
                author.uuid = uuid4()
            session.execute(insert_author.format(entry_id=entry_id, role='coAuthor', order=idx + 2, **author.model_dump()))

    # add the details
    if payload.details is not None and len(payload.details) > 0:
        detail_sql = load_sql('insert_detail.sql')
        for detail in payload.details:
            # handle the data type
            detail_payload = {k: i for k, i in detail.model_dump() if k != 'value'}
            detail_payload['raw_value'] = detail.value if isinstance(detail.value, dict) else {'__literal__': detail.value}
            session.execute(detail_sql.format(entry_id=entry_id, **detail_payload))
