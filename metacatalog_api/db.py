from typing import List
from pathlib import Path

from sqlmodel import Session, text
from psycopg2.errors import UndefinedTable
from sqlalchemy.exc import ProgrammingError
from pydantic_geojson import FeatureCollectionModel
from pydantic import BaseModel

from metacatalog_api import models
from sqlmodel import select, exists, col

DB_VERSION = 3
SQL_DIR = Path(__file__).parent / "sql"

# helper function to load sql files
def load_sql(file_name: str) -> str:
    path = Path(file_name)
    if not path.exists():
        path = SQL_DIR / file_name
    
    with open(path, 'r') as f:
        return f.read()


# helper function to check the database version
def get_db_version(session: Session, schema: str = 'public') -> dict:
    try:
        v = session.exec(text(f"SELECT db_version FROM {schema}.metacatalog_info order by db_version desc limit 1;")).scalar() 
    except UndefinedTable:
        v = 0
    except ProgrammingError as e:
        if 'relation "metacatalog_info"' in str(e):
            v = 0
        else:
            raise e
    return {'db_version': v}


def check_db_version(session: Session, schema: str = 'public') -> bool:
    """Verify that the database version matches the expected version.
    
    Args:
        session: A SQLAlchemy session object
        
    Raises:
        ValueError: If database version doesn't match DB_VERSION constant

    Returns:
        bool: True if database version matches
    """
    remote_db_version = get_db_version(session, schema=schema)['db_version']
    if remote_db_version != DB_VERSION:
        raise ValueError(
            f"Database version mismatch. Expected {DB_VERSION}, got {remote_db_version}. "
            "Please run database migrations to update your schema."
        )
    return True


def install(session: Session, schema: str = 'public', populate_defaults: bool = True) -> None:
    # get the install script
    install_sql = load_sql(SQL_DIR / 'maintain' /'install.sql').format(schema=schema)

    # execute the install script
    session.exec(text(install_sql))
    session.commit()

    # populate the defaults
    if populate_defaults:
        populate_sql = load_sql(SQL_DIR / 'maintain' / 'defaults.sql').replace('{schema}', schema)
        session.exec(text(populate_sql))
        session.commit()
    
    # set the current version to the remote database
    session.exec(text(f"INSERT INTO {schema}.metacatalog_info (db_version) VALUES ({DB_VERSION});"))
    session.commit()


def check_installed(session: Session, schema: str = 'public') -> bool:
    try:
        info = session.exec(text(f"SELECT * FROM information_schema.tables WHERE table_schema = '{schema}' AND table_name = 'entries'")).first() 
        return info is not None
    except Exception:
        return False
    

def get_entries(session: Session, limit: int = None, offset: int = None, variable: str | int = None, title: str = None) -> list[models.Metadata]:
    # build the base query
    sql = select(models.EntryTable)

    # handle variable filter
    if isinstance(variable, int):
        sql = sql.join(models.VariableTable).where(models.VariableTable.id == variable)
    elif isinstance(variable, str):
        sql = sql.join(models.VariableTable).where(col(models.VariableTable.name).ilike(variable))
    
    # handle title filter
    if title is not None:
        sql = sql.where(col(models.EntryTable.title).ilike(title))
    
    # handle offset and limit
    sql = sql.offset(offset).limit(limit)

    # execute the query
    entries = session.exec(sql).all()  

    return [models.Metadata.model_validate(entry) for entry in entries]


def get_entries_by_id(session: Session, entry_ids: int | list[int], limit: int = None, offset: int = None) -> list[models.Metadata] | models.Metadata:
    # base query
    sql = select(models.EntryTable)

    # handle entry ids
    if isinstance(entry_ids, int):
        sql = sql.where(models.EntryTable.id == entry_ids)
    elif isinstance(entry_ids, (list, tuple)):
        sql = sql.where(col(models.EntryTable.id).in_(entry_ids))

    # handle offset and limit
    sql = sql.offset(offset).limit(limit)

    # run the query
    entries = session.exec(sql).all()

    if isinstance(entries, models.EntryTable):
        return models.Metadata.model_validate(entries)
    else:
        return [models.Metadata.model_validate(entry) for entry in entries]


def get_entries_locations(session: Session, ids: List[int] = None, limit: int = None, offset: int = None) -> FeatureCollectionModel:
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
    result = session.exec(text(sql)).one()[0]
        
    if result['features'] is None:
        return dict(type="FeatureCollection", features=[])
    
    return result
    

class SearchResult(BaseModel):
    id: int
    matches: list[str]
    weight: int


def search_entries(session: Session, search: str, full_text: bool = True, limit: int = None, offset: int = None, variable: int | str = None) -> list[SearchResult]:
    # build the limit and offset
    lim = f" LIMIT {limit} " if limit is not None else ""
    off = f" OFFSET {offset} " if offset is not None else ""
    filt = ""
    params = {"lim": lim, "off": off}
    # handle variable filter
    if isinstance(variable, int):
        filt = " WHERE entries.variable_id = :variable "
        params["variable"] = variable
    elif isinstance(variable, str):
        variable = get_variables(session, name=variable)
        filt = " WHERE entries.variable_id in (:variabe) "
        params["variable"] = [v.id for v in variable]

    # handle full text search
    if full_text:
        search = '&'.join(search.split(' '))
        params["prompt"] = search
        base_query = "ftl_search_entries.sql"
    else:
        base_query = "search_entries.sql"
        params["prompt"] = search
    # get the sql for the query
    sql = load_sql(base_query).format(limit=lim, offset=off, filter=filt)
    #sql = load_sql(base_query)

    # execute the query
    mappings = session.exec(text(sql), params=params).mappings().all()

    return mappings


def get_authors(session: Session, search: str = None, exclude_ids: list[int] = None, limit: int = None, offset: int = None) -> List[models.Author]:
    # build the base query
    query = select(models.PersonTable)

    # handle search
    if search is not None:
        search = search.replace('*', '%')
        
        query = query.where(
            col(models.PersonTable.first_name).contains(search) |
            col(models.PersonTable.last_name).contains(search) |
            col(models.PersonTable.organisation_name).contains(search)
        )
    
    # handle exclude
    if exclude_ids is not None:
        query = query.where(
            col(models.PersonTable.id).not_in(exclude_ids)
        )
    
    # hanlde limit and offset
    query = query.offset(offset).limit(limit)

    # run
    authors = session.exec(query).all()

    return [models.Author.model_validate(author) for author in authors]


def get_authors_by_name(session: Session, name: str, limit: int = None, offset: int = None) -> list[models.Author]:
    if '*' in name:
        name = name.replace('*', '%')
    if '%' not in name:
        name = f'%{name}%'
    
    # limit and offset
    lim = f" LIMIT {limit} " if limit is not None else ""
    off = f" OFFSET {offset} " if offset is not None else ""

    sql = load_sql("authors_by_name.sql").format(limit=lim, offset=off)
    authors = session.exec(text(sql), params={"prompt": name}).all()

    return [models.Author.model_validate(author) for author in authors]


def get_author_by_name(session: Session, name: str, strict: bool = False) -> models.Author:
    authors = get_authors_by_name(session, name)
    if len(authors) == 0:
        return None
    if strict and len(authors) > 1:
        raise RuntimeError(f"More than one author found for name {name}")
    else:
        return authors[0]


def create_or_get_author(session: Session, author: models.AuthorCreate) -> models.Author:
    sql = select(models.PersonTable).where(
        models.PersonTable.first_name == author.first_name &
        models.PersonTable.last_name == author.last_name &
        models.PersonTable.organisation_name == author.organisation_name &
        models.PersonTable.organisation_abbrev == author.organisation_abbrev
    )

    author = session.exec(sql).first()
    if author is None:
        session.add(models.PersonTable.model_validate(author))
        session.commit()
        session.refresh(author)
    return models.Author.model_validate(author)


def add_author(session: Session, author: models.AuthorCreate) -> models.Author:
    author = models.PersonTable.model_validate(author)
    
    session.add(author)
    session.commit()
    session.refresh(author)

    return models.Author.model_validate(author) 


def get_authors_by_entry(session: Session, entry_id: int) -> list[models.Author]:
    query = (
        select(models.PersonTable).where(models.PersonTable.id.in_(
                select(models.EntryTable.author_id)
                .where(models.EntryTable.id == entry_id)
            )
        ).union_all(
            select(models.PersonTable).join(models.NMPersonEntries)
            .where(models.NMPersonEntries.entry_id == entry_id)
            .order_by(col(models.NMPersonEntries.order).asc()) 
        )
    )
    authors = session.exec(query).all()

    return [models.Author.model_validate(author) for author in authors]


def get_author_by_id(session: Session, id: int) -> models.Author:   
    # execute the query
    author = session.exec(select(models.PersonTable).where(models.PersonTable.id == id)).first()

    if author is None:
        raise ValueError(f"Author with id {id} not found")
    else:
        return models.Author.model_validate(author)


def get_variables(session: Session, limit: int = None, offset: int = None, name: str = None) -> list[models.Variable]:
    # build the query
    query = select(models.VariableTable)
    if name is not None:
        query = query.where(col(models.VariableTable.name).ilike(name))
    variables = session.exec(query.offset(offset).limit(limit))

    return [models.Variable.model_validate(var) for var in variables]

    
def get_available_variables(session: Session, limit: int = None, offset: int = None) -> list[models.Variable]:
    # build the query
    query = select(models.VariableTable).where(
        exists(select(models.EntryTable.id).where(models.EntryTable.variable_id == models.VariableTable.id))
    ).offset(offset).limit(limit)
    
    # execute the query
    variables = session.exec(query).all()

    return [models.Variable.model_validate(var) for var in variables]


def get_variable_by_id(session: Session, id: int) -> models.Variable:
    variable = session.get(models.VariableTable, id)

    if variable is None:
        raise ValueError(f"Variable with id {id} not found")
    
    return models.Variable.model_validate(variable)


def get_licenses(session: Session, limit: int = None, offset: int = None) -> List[models.License]:
    # get the licenses
    licenses = session.exec(
        select(models.LicenseTable).offset(offset).limit(limit)
    ).all()

    return [models.License.model_validate(lic) for lic in licenses]


def get_license_by_id(session: Session, id: int) -> models.License:
    # get the one license in question
    lic = session.get(models.LicenseTable, id)
    if lic is None:
        raise ValueError(f"License with id {id} not found")
    else:
        return models.License.model_validate(lic)


def get_datatypes(session: Session, id: int = None) -> list[models.DatasourceTypeBase]:
    # handle the id
    if id is not None:
        sql = select(models.DatasourceTypeTable).where(models.DatasourceTypeTable.id == id)
        type_ = session.exec(sql).one()
        return models.DatasourceTypeBase.model_validate(type_)
    else:
        # get all the types
        types = session.exec(select(models.DatasourceTypeTable)).all()

        return [models.DatasourceTypeBase.model_validate(type_) for type_ in types]


def add_entry(session: Session, payload: models.EntryCreate, author_duplicates: bool = False) -> models.Metadata:
    # grab the keywords
    if payload.keywords is not None and len(payload.keywords) > 0:
        sql = select(models.KeywordTable).where(col(models.KeywordTable.id).in_(payload.keywords))
        keywords =  session.exec(sql).all()
    else:
        keywords = []
    
    # add or set the author
    if isinstance(payload.author, int):
        author = session.get(models.PersonTable, payload.author)
    elif not author_duplicates:
        author = create_or_get_author(session, payload.author)
    else:
        author = models.PersonTable.model_validate(payload.author)
    
    # handle co-authors
    if payload.coAuthors is None or len(payload.coAuthors) == 0:
        coAuthors = []
    else:
        coAuthors = []
        for coAuthor in payload.coAuthors:
            if isinstance(coAuthor, int):
                coAuthors.append(session.get(models.PersonTable, coAuthor))
            elif not author_duplicates:
                coAuthors.append(create_or_get_author(session, coAuthor))
            else:
                coAuthors.append(models.PersonTable.model_validate(coAuthor))
    
    # handle license
    if isinstance(payload.license, int):
        license = session.get(models.LicenseTable, payload.license)
    else:
        license = models.LicenseCreate.model_validate(payload.license)

    # create the table entry
    entry = models.EntryTable(
        title=payload.title,
        abstract=payload.abstract,
        external_id=payload.external_id,
        #location=payload.location,
        version=payload.version,
        is_partial=payload.is_partial,
        comment=payload.comment,
        citation=payload.citation,
        #embargo=payload.embargo,
        #embargo_end=payload.embargo_end,
        license=license,
        variable_id=payload.variable,
        author=author,
        coAuthors=coAuthors,
        keywords=keywords
    )
    if payload.location is not None:
        entry.location = models.EntryTable.validate_location(payload.location, None)

    # add
    session.add(entry)
    session.commit()

        # build the details
    if payload.details is not None and len(payload.details) > 0:
        details = []
        for d in payload.details:
            details.append(models.DetailTable(
                key=d.key, 
                raw_value=d.raw_value,
                entry_id=entry.id,
                thesaurus_id=d.thesaurus,
                title=d.title,
                description=d.description
            ))
        entry.details = details
        session.add(entry)
        session.commit()

    # refresh the entry object and validate the Metadata model
    session.refresh(entry)
    return models.Metadata.model_validate(entry)


def add_datasource(session: Session, entry_id: int, datasource: models.DatasourceCreate) -> models.Metadata:
    # get the entry
    entry = session.get(models.EntryTable, entry_id)
    if entry is None:
        raise ValueError(f"Entry with id {entry_id} not found")
    # look up the datasource type
    if isinstance(datasource.type, str):
        sql = select(models.DatasourceTypeTable.id).where(col(models.DatasourceTypeTable.name) == datasource.type)
    else:
        sql = select(models.DatasourceTypeTable.id).where(models.DatasourceTypeTable.id == datasource.type)
    
    # get the datasource type id
    datasource_type_id = session.exec(sql).first()
    if datasource_type_id is None:
        raise ValueError(f"Datasource type with name or id {datasource.type} was not found in the database")
    
    # check if a temporal scale is provided
    if datasource.temporal_scale is not None:
        temporal_scale = models.TemporalScaleTable.model_validate(datasource.temporal_scale)
    else:
        temporal_scale = None
    
    # check if a spatial scale is provided
    if datasource.spatial_scale is not None:
        spatial_scale = models.SpatialScaleTable.model_validate(datasource.spatial_scale)
    else:
        spatial_scale = None

    # create the table entry
    datasource = models.DatasourceTable(
        path=datasource.path,
        encoding=datasource.encoding,
        type_id=datasource_type_id,
        args=datasource.args if datasource.args is not None else {},
        temporal_scale=temporal_scale,
        spatial_scale=spatial_scale,
        variable_names=datasource.variable_names if datasource.variable_names is not None else []
    )

    # add the datasource
    entry.datasource = datasource
    session.add(entry)
    session.commit()

    session.refresh(entry)
    return models.Metadata.model_validate(entry)


def get_grouptypes(session: Session) -> list[models.EntryGroupType]:
    types = session.exec(select(models.EntryGroupTypeTable)).all()
    return [models.EntryGroupType.model_validate(t) for t in types]


def get_groups(session: Session, title: str = None, description: str = None, type: str = None, entry_id: int = None, limit: int = None, offset: int = None, with_metadata: bool = False) -> list[models.EntryGroup] | list[models.EntryGroupWithMetadata]:
    sql = select(models.EntryGroupTable)

    if title is not None:
        sql = sql.where(models.EntryGroupTable.title == title)
    if description is not None:
        sql = sql.where(col(models.EntryGroupTable.description).ilike(description))
    if type is not None:
        sql = sql.join(models.EntryGroupTypeTable).where(models.EntryGroupTypeTable.name == type)
    if entry_id is not None:
        sql = sql.join(models.NMGroupsEntries).where(models.NMGroupsEntries.entry_id == entry_id)
    
    if limit is not None:
        sql = sql.limit(limit)
    if offset is not None:
        sql = sql.offset(offset)
    
    groups = session.exec(sql).all()
    if with_metadata:
        return [models.EntryGroupWithMetadata.model_validate(g) for g in groups]
    else:
        return [models.EntryGroup.model_validate(g) for g in groups]


def get_group(session: Session, id: int = None, title: str = None, with_metadata: bool = False) -> models.EntryGroupWithMetadata | models.EntryGroup | None:
    if id is None and title is None:
        raise ValueError('Either id or title has to be given')
    
    sql = select(models.EntryGroupTable)
    if id is not None:
        sql = sql.where(models.EntryGroupTable.id == id)
    else:
        sql = sql.where(models.EntryGroupTable.title == title)
    
    group = session.exec(sql).first()
    if group is None:
        return None
    if with_metadata:
        return models.EntryGroupWithMetadata.model_validate(group)
    else:
        return models.EntryGroup.model_validate(group)


def add_group(session: Session, title: str, description: str, type: str, entry_ids: list[int] = []) -> models.EntryGroup:
    types = get_grouptypes(session=session)
    grouptype = next(filter(lambda t: t.name.lower() == type.lower(), types), None)
    if grouptype is None:
        raise ValueError(f"The type {type} is not valid. Maybe you misspelled? Supported types: [{','.join([t.title for t in types])}]")
    
    group = models.EntryGroupTable(
        title=title,
        description=description,
        type_id=grouptype.id
    )

    session.add(group)
    session.commit()
    session.refresh(group)

    if len(entry_ids) > 0:
        for entry_id in entry_ids:
            session.add(models.NMGroupsEntries(entry_id=entry_id, group_id=group.id))
        session.commit()

    return models.EntryGroup.model_validate(group)

def group_entries(session: Session, group: models.EntryGroupBase | int, entry_ids: list[int | models.EntryBase]) -> models.EntryGroup:
    # get the group
    if isinstance(group, int):
        group_id = group
    elif hasattr(group, 'id') and group.id is not None:
        group_id = group.id
    else:
        new_group = get_group(session=session, title=group.title)
        if new_group is None:
            group = add_group(session=session, title=group.title, description=group.description, type=group.type)
        else:
            group = new_group
        group_id = group.id
    
    for entry_id in entry_ids:
        if not isinstance(entry_id, int):
            entry_id = entry_id.id 
        session.add(models.NMGroupsEntries(group_id=group_id, entry_id=entry_id))
    session.commit()

    group = get_group(session=session, id=group_id)
    return models.EntryGroup.model_validate(group)