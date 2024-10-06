from typing import List, Dict
from pathlib import Path

from models import Author, Metadata
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
    result = session.execute(sql).fetchone()

    return result['json_build_object']


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


def get_authors(session: Cursor, search: str = None) -> List[Author]:
    # build the filter
    filt = ""
    if search is not None:
        filt = f"WHERE last_name LIKE {search} OR first_name LIKE {search} OR organisation_name LIKE {search}"
    
    # build the basic query
    sql = load_sql("get_authors.sql").format(filter=filt)

    # execute the query
    results = session.execute(sql).all()

    return [Author(**result) for result in results]


def get_entry_authors(session: Cursor, entry_id: int) -> List[Author]:
    # build the query
    sql = load_sql("get_entry_authors.sql").format(entry_id=entry_id)

    # execute the query
    results = session.execute(sql).all()

    return [Author(**result) for result in results]