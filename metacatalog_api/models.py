from typing import Optional, Annotated
from datetime import timedelta
import json

from pydantic import field_validator
from pydantic_geojson import PointModel, PolygonModel
from sqlmodel import Field, SQLModel, Column, Relationship
from sqlmodel import JSON, ARRAY, String, Text
from pydantic import UUID4, HttpUrl
from uuid import uuid4
from geoalchemy2 import Geometry, WKBElement
from geoalchemy2.shape import to_shape
from shapely import to_geojson, from_geojson
from shapely.wkt import loads, dumps
from datetime import datetime
from dateutil.relativedelta import relativedelta


def get_embargo_end(value=None):
    if value is None:
        value = datetime.now()
    return value + relativedelta(years=2)


class PersonRole(SQLModel, table=True):
    __tablename__ = 'person_roles'

    # columns
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(nullable=False, unique=True)
    description: str | None = None


class NMPersonEntries(SQLModel, table=True):
    __tablename__ = 'nm_persons_entries'

    person_id: int = Field(foreign_key='persons.id', primary_key=True)
    entry_id: int = Field(foreign_key='entries.id', primary_key=True)
    relationship_type_id: int = Field(default=13, foreign_key='person_roles.id')
    order: int = Field(default=1)

class PersonBase(SQLModel):
    is_organisation: bool = False
    first_name: str | None = None
    last_name: str | None = None
    organisation_name: str | None = None
    organisation_abbrev: str | None = None
    affiliation: str | None = None
    attribution: str | None = None

class PersonTable(PersonBase, table=True):
    __tablename__ = 'persons'
    id: int | None = Field(default=None, primary_key=True)
    uuid: UUID4 = Field(default_factory=uuid4)
    entries: list['EntryTable'] = Relationship(back_populates='author')

class Author(PersonBase):
    id: int
    uuid: UUID4

class CoAuthor(PersonBase):
    id: int
    uuid: UUID4

class AuthorCreate(PersonBase):
    pass

class LicenseBase(SQLModel):
    short_title: str = Field(nullable=False, unique=True)
    title: str = Field(nullable=False)
    summary: str
    full_text: str | None = None
    link: str | None = None
    by_attribution: bool = False
    share_alike: bool = False
    commercial_use: bool = False

class LicenseTable(LicenseBase, table=True):
    __tablename__ = 'licenses'
    id: int | None = Field(default=None, primary_key=True) 
    entries: list['EntryTable'] = Relationship(back_populates='license')

class LicenseCreate(LicenseBase):
    pass

class License(LicenseBase):
    id: int

class ThesaurusBase(SQLModel):
    uuid: UUID4 = Field(default_factory=uuid4)
    name: str = Field(nullable=False, unique=True)
    title: str = Field(nullable=False)
    organisation: str = Field(nullable=False)
    description: str | None = None
    url: HttpUrl = Field(sa_column=Column(Text, nullable=False))

class ThesaurusTable(ThesaurusBase, table=True):
    __tablename__ = 'thesaurus'
    id: int | None = Field(default=None, primary_key=True)

class Thesaurus(ThesaurusBase):
    id: int

class NMKeywordsEntries(SQLModel, table=True):
    __tablename__ = 'nm_keywords_entries'
    keyword_id: int = Field(foreign_key='keywords.id', primary_key=True)
    entry_id: int = Field(foreign_key='entries.id', primary_key=True)


class KeywordBase(SQLModel):
    id: int | None = None
    uuid: UUID4 | None = None
    parent_id: int | None = Field(foreign_key='keywords.id')
    value: str = Field(nullable=False)
    full_path: str | None = None

class KeywordTable(KeywordBase, table=True):
    __tablename__ = 'keywords'
    id: int = Field(primary_key=True)
    uuid: UUID4 = Field(default_factory=uuid4)
    thesaurus_id: int = Field(foreign_key='thesaurus.id')

    # relationships
    thesaurus: ThesaurusTable = Relationship()
    entries: list['EntryTable'] = Relationship(back_populates='keywords', link_model=NMKeywordsEntries)

class Keyword(KeywordBase):
    thesaurus: ThesaurusBase


class UnitBase(SQLModel):
    name: str = Field(nullable=False, unique=True)
    symbol: str = Field(nullable=False)
    si: str | None = None

class UnitTable(UnitBase, table=True):
    __tablename__ = 'units'
    id: int | None = Field(default=None, primary_key=True)
    variables: list['VariableTable'] = Relationship(back_populates='unit')

class Unit(UnitBase):
    pass

class VariableBase(SQLModel):
    name: str = Field(nullable=False, unique=True)
    symbol: str = Field(nullable=False)
    column_names: list[str] = Field(sa_column=Column(ARRAY(String)))

class VariableTable(VariableBase, table=True):
    __tablename__ = 'variables'

    # columns
    id: int | None = Field(default=None, primary_key=True)
    unit_id: int = Field(foreign_key='units.id')
    keyword_id: int | None = Field(foreign_key='keywords.id')

    # relationships
    unit: UnitTable = Relationship(back_populates='variables')
    entries: list['EntryTable'] = Relationship(back_populates='variable')
    keyword: list[KeywordTable] = Relationship()

class Variable(VariableBase):
    id: int
    unit: Unit
    keyword: Keyword | None = None

class DetailBase(SQLModel):
    key: str
    stem: str | None = None
    title: str | None = None
    raw_value: dict = Field(sa_column=Column(JSON), default={})
    description: str | None = None

    @field_validator('raw_value', mode='before')
    def validate_raw_value(cls, v, info):
        if v is None:
            return {}
        elif not isinstance(v, dict):
            return {'__literal__': v}
        else:
            return v

class DetailTable(DetailBase, table=True):
    __tablename__ = 'details'
    id: int | None = Field(default=None, primary_key=True)
    entry_id: int = Field(foreign_key='entries.id')
    thesaurus_id: int | None = Field(foreign_key='thesaurus.id', default=None)

    entry: 'EntryTable' = Relationship(back_populates='details')
    thesaurus: ThesaurusTable = Relationship()


class Detail(DetailBase):
    thesaurus: ThesaurusBase | None = None

    @property
    def value(self):
        # check if the raw_value has a literal value
        if '__literal__' in self.raw_value:
            return self.raw_value['__literal__']
        else:
            return self.raw_value

class DetailCreate(DetailBase):
    thesaurus: int | None = None

class DatasourceTypeBase(SQLModel):
    id: int | None = None
    name: str
    title: str
    description: str | None = None

class DatasourceTypeTable(DatasourceTypeBase, table=True):
    __tablename__ = 'datasource_types'
    id: int = Field(primary_key=True)
    datasources: list['DatasourceTable'] = Relationship(back_populates='type')

class TemporalScaleBase(SQLModel):
    id: int | None = None
    resolution: timedelta
    observation_start: datetime
    observation_end: datetime
    support: float
    dimension_names: list[str] = Field(sa_column=Column(ARRAY(String)))

class TemporalScaleTable(TemporalScaleBase, table=True):
    __tablename__ = 'temporal_scales'
    id: int | None = Field(default=None, primary_key=True)
    datasources: list['DatasourceTable'] = Relationship(back_populates='temporal_scale')

class TemporalScale(TemporalScaleBase):
    @property
    def extent(self):
        return [self.observation_start, self.observation_end]


class SpatialScaleBase(SQLModel):
    id: int | None = None
    resolution: int
    extent: Optional[Annotated[PolygonModel, Field(sa_column=Column(Geometry(geometry_type='POLYGON', srid=4326), nullable=True))]] = None
    support: float
    dimension_names: list[str] = Field(sa_column=Column(ARRAY(String)))

    @field_validator('extent', mode='before')
    def validate_extent(cls, v, info):
        if v is None:
            return None
        elif isinstance(v, str):
            shape = loads(v)
            js = json.loads(to_geojson(shape))
            poly = PolygonModel.model_validate(js)
        elif isinstance(v, (list, tuple)):
            poly = PolygonModel(coordinates=v)
        elif isinstance(v, WKBElement):
            shape = to_shape(v)
            js = json.loads(to_geojson(shape))
            poly = PolygonModel.model_validate(js)
        elif isinstance(v, dict):
            poly = PolygonModel(**v)
        elif isinstance(v, PolygonModel):
            poly = v
        else:
            raise ValueError(f"Invalid geometry type: {v} ({type(v)})")

        return poly

class SpatialScaleTable(SpatialScaleBase, table=True):
    __tablename__ = 'spatial_scales'
    id: int | None = Field(default=None, primary_key=True)
    extent: Optional[str] = Field(sa_column=Column(Geometry(geometry_type='POLYGON', srid=4326), nullable=True))
    datasources: list['DatasourceTable'] = Relationship(back_populates='spatial_scale')

    @field_validator('extent', mode='before')
    def validate_extent(cls, v, info):
        if v is None:
            return None
        elif isinstance(v, str):
            shape = loads(v)
        elif isinstance(v, PolygonModel):
            shape = from_geojson(v.model_dump_json())
        elif isinstance(v, WKBElement):
            shape = to_shape(v)
        else:
            raise ValueError(f"Can't transform extent back to WKBElement: {v} ({type(v)})")
        return  dumps(shape)

class SpatialScale(SpatialScaleBase):
    pass

class DatasourceBase(SQLModel):
    path: str
    encoding: str = 'utf-8'
    variable_names: list[str] = Field(sa_column=Column(ARRAY(String)))
    args: dict | None = Field(sa_column=Column(JSON))

class DatasourceTable(DatasourceBase, table=True):
    __tablename__ = 'datasources'
    
    # columns
    id: int | None = Field(default=None, primary_key=True)
    type_id: int = Field(foreign_key='datasource_types.id')
    temporal_scale_id: int | None = Field(foreign_key='temporal_scales.id')
    spatial_scale_id: int | None = Field(foreign_key='spatial_scales.id')

    # relationships
    type: DatasourceTypeTable = Relationship(back_populates='datasources')
    temporal_scale: TemporalScaleTable = Relationship(back_populates='datasources')
    spatial_scale: SpatialScaleTable = Relationship(back_populates='datasources')
    entry: 'EntryTable' = Relationship(back_populates='datasource')

class DatasourceCreate(DatasourceBase):
    type: int | str
    temporal_scale: TemporalScale | None = None
    spatial_scale: SpatialScale | None = None

class Datasource(DatasourceBase):
    id: int
    type: DatasourceTypeBase
    temporal_scale: TemporalScale | None = None
    spatial_scale: SpatialScale | None = None

class EntryBase(SQLModel):
    title: str = Field(nullable=False, unique=True)
    abstract: str
    external_id: str | None = None
    location: Optional[Annotated[PointModel, Field(sa_column=Column(Geometry(geometry_type='POINT', srid=4326), nullable=True, default=None))]] = None
    version: int  = 1
    latest_version_id: int | None = None
    is_partial: bool = False
    comment: str | None = None
    citation: str | None = None
    embargo: bool = False
    embargo_end: datetime | None = None
    publication: datetime | None = None
    lastUpdate: datetime | None = None
    
    @field_validator('location', mode='before')
    def validate_location(cls, v, info):
        if v is None:
            return None
        elif isinstance(v, (list, tuple)):
            point = PointModel(coordinates=v)
        elif isinstance(v, WKBElement):
            shape = to_shape(v)
            js = json.loads(to_geojson(shape))
            point = PointModel.model_validate(js)
        elif isinstance(v, dict):
            point = PointModel(**v)
        elif isinstance(v, str):
            shape = loads(v)
            js = json.loads(to_geojson(shape))
            point = PointModel.model_validate(js)
        elif isinstance(v, PointModel):
            point = v
        else:
            raise ValueError(f"Invalid location type: {v} ({type(v)})")
        
        return point

class EntryTable(EntryBase, table=True):
    __tablename__ = 'entries'

    # columns
    id: int | None = Field(default=None, primary_key=True)
    uuid: UUID4 = Field(default_factory=uuid4)
    location: Optional[str] = Field(sa_column=Column(Geometry(geometry_type='POINT', srid=4326), nullable=True, default=None))
    author_id: int | None = Field(foreign_key='persons.id')
    license_id: int | None = Field(default=None, foreign_key="licenses.id")
    variable_id: int = Field(foreign_key='variables.id')
    datasource_id: int | None = Field(foreign_key = 'datasources.id')
    
    # add the datetime fields
    embargo_end: datetime = Field(default_factory=get_embargo_end)
    publication: datetime = Field(default_factory=datetime.now)
    lastUpdate: datetime = Field(default_factory=datetime.now)


    # relationships
    license: LicenseTable = Relationship(back_populates='entries')
    author: PersonTable = Relationship()
    coAuthors: list[PersonTable] = Relationship(link_model=NMPersonEntries)
    variable: VariableTable = Relationship(back_populates='entries')
    keywords: list[KeywordTable] = Relationship(back_populates='entries', link_model=NMKeywordsEntries)
    details: list[DetailTable] = Relationship(back_populates='entry')
    datasource: DatasourceTable = Relationship(back_populates='entry')

    @field_validator('location', mode='before')
    def validate_location(cls, v, info):
        if v is None:
            return None
        elif isinstance(v, str):
            shape = loads(v)
        elif isinstance(v, dict):
            shape = from_geojson(PointModel.model_validate(v).model_dump_json())
        elif isinstance(v, PointModel):
            shape = from_geojson(v.model_dump_json())
        elif isinstance(v, WKBElement):
            shape = to_shape(v)
        else:
            raise ValueError(f"Can't transform location back to WKBElement: {v} ({type(v)})")
        return  dumps(shape)


class EntryCreate(EntryBase):
    license: LicenseCreate | int
    variable: int
    author: AuthorCreate | int
    coAuthors: list[AuthorCreate | int] | None = None
    keywords: list[int] | None = None
    details: list[DetailCreate] | None = None
    datasource: Datasource | None = None


class Metadata(EntryBase):
    id: int
    uuid: UUID4
    license: License | None
    variable: Variable
    author: Author
    coAuthors: list[CoAuthor] = []
    keywords: list[Keyword] = []
    details: list[Detail] = []
    datasource: Datasource | None = None
    # associated_groups: List['EntryGroup'] = relationship("EntryGroup", secondary="nm_entrygroups", back_populates='entries')

