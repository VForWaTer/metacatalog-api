// TypeScript definitions for metacatalog models
// Based on metacatalog_api/models.py

export interface Point {
  type: 'Point';
  coordinates: [number, number]; // [longitude, latitude]
}

export interface Polygon {
  type: 'Polygon';
  coordinates: number[][][]; // Array of linear rings
}

export interface Geometry {
  type: string;
  coordinates: any;
}

// Base interfaces
export interface PersonBase {
  is_organisation: boolean;
  first_name?: string;
  last_name?: string;
  organisation_name?: string;
  organisation_abbrev?: string;
  affiliation?: string;
  attribution?: string;
  orcid?: string;
}

export interface PersonTable extends PersonBase {
  id?: number;
  uuid: string;
  entries?: EntryTable[];
}

export interface Author extends PersonBase {
  id: number;
  uuid: string;
}

export interface CoAuthor extends PersonBase {
  id: number;
  uuid: string;
}

export interface AuthorCreate extends PersonBase {}

export interface PersonRole {
  id?: number;
  name: string;
  description?: string;
}

export interface NMPersonEntries {
  person_id: number;
  entry_id: number;
  relationship_type_id: number;
  order: number;
}

// License models
export interface LicenseBase {
  short_title: string;
  title: string;
  summary: string;
  full_text?: string;
  link?: string;
  by_attribution: boolean;
  share_alike: boolean;
  commercial_use: boolean;
}

export interface LicenseTable extends LicenseBase {
  id?: number;
  entries?: EntryTable[];
}

export interface LicenseCreate extends LicenseBase {}

export interface License extends LicenseBase {
  id: number;
}

// Thesaurus models
export interface ThesaurusBase {
  uuid: string;
  name: string;
  title: string;
  organisation: string;
  description?: string;
  url: string;
}

export interface ThesaurusTable extends ThesaurusBase {
  id?: number;
}

export interface Thesaurus extends ThesaurusBase {
  id: number;
}

// Keyword models
export interface NMKeywordsEntries {
  keyword_id: number;
  entry_id: number;
}

export interface KeywordBase {
  id?: number;
  uuid?: string;
  parent_id?: number;
  value: string;
  full_path?: string;
}

export interface KeywordTable extends KeywordBase {
  id: number;
  uuid: string;
  thesaurus_id: number;
  thesaurus?: ThesaurusTable;
  entries?: EntryTable[];
}

export interface Keyword extends KeywordBase {
  thesaurus: ThesaurusBase;
}

// Unit models
export interface UnitBase {
  name: string;
  symbol: string;
  si?: string;
}

export interface UnitTable extends UnitBase {
  id?: number;
  variables?: VariableTable[];
}

export interface Unit extends UnitBase {}

// Variable models
export interface VariableBase {
  name: string;
  symbol: string;
  column_names: string[];
}

export interface VariableTable extends VariableBase {
  id?: number;
  unit_id: number;
  keyword_id?: number;
  unit?: UnitTable;
  entries?: EntryTable[];
  keyword?: KeywordTable[];
}

export interface Variable extends VariableBase {
  id: number;
  unit: Unit;
  keyword?: Keyword;
}

// Detail models
export interface DetailBase {
  key: string;
  stem?: string;
  title?: string;
  raw_value: Record<string, any>;
  description?: string;
}

export interface DetailTable extends DetailBase {
  id?: number;
  entry_id: number;
  thesaurus_id?: number;
  entry?: EntryTable;
  thesaurus?: ThesaurusTable;
}

export interface Detail extends DetailBase {
  thesaurus?: ThesaurusBase;
  value?: any; // Computed property
}

export interface DetailCreate extends DetailBase {
  thesaurus?: number;
}

// Datasource type models
export interface DatasourceTypeBase {
  id?: number;
  name: string;
  title: string;
  description?: string;
}

export interface DatasourceTypeTable extends DatasourceTypeBase {
  id: number;
  datasources?: DatasourceTable[];
}

// Temporal scale models
export interface TemporalScaleBase {
  resolution: string; // ISO 8601 duration string
  observation_start: string; // ISO 8601 datetime
  observation_end: string; // ISO 8601 datetime
  support: number;
  dimension_names: string[];
}

export interface TemporalScaleTable extends TemporalScaleBase {
  id?: number;
  datasources?: DatasourceTable[];
}

export interface TemporalScale extends TemporalScaleBase {
  extent?: [string, string]; // [observation_start, observation_end]
}

// Spatial scale models
export interface SpatialScaleBase {
  resolution: number;
  extent?: Polygon;
  support: number;
  dimension_names: string[];
}

export interface SpatialScaleTable {
  id?: number;
  resolution: number;
  extent?: string; // WKT string
  support: number;
  dimension_names: string[];
  datasources?: DatasourceTable[];
}

export interface SpatialScale extends SpatialScaleBase {}

// Datasource models
export interface DatasourceBase {
  path: string;
  encoding: string;
  variable_names: string[];
  args?: Record<string, any>;
}

export interface DatasourceTable extends DatasourceBase {
  id?: number;
  type_id: number;
  temporal_scale_id?: number;
  spatial_scale_id?: number;
  type?: DatasourceTypeTable;
  temporal_scale?: TemporalScaleTable;
  spatial_scale?: SpatialScaleTable;
  entry?: EntryTable;
}

export interface DatasourceCreate extends DatasourceBase {
  type: number | string;
  temporal_scale?: TemporalScaleBase;
  spatial_scale?: SpatialScaleBase;
}

export interface Datasource extends DatasourceBase {
  id: number;
  type: DatasourceTypeBase;
  temporal_scale?: TemporalScale;
  spatial_scale?: SpatialScale;
}

// Entry group models
export interface NMGroupsEntries {
  entry_id: number;
  group_id: number;
}

export interface EntryGroupTypeBase {
  name: string;
  description: string;
}

export interface EntryGroupTypeTable extends EntryGroupTypeBase {
  id?: number;
  groups?: EntryGroupTable[];
}

export interface EntryGroupType extends EntryGroupTypeBase {
  id?: number;
  uuid?: string;
}

export interface EntryGroupBase {
  title: string;
  description?: string;
  publication?: string; // ISO 8601 datetime
  lastUpdate?: string; // ISO 8601 datetime
}

export interface EntryGroupTable extends EntryGroupBase {
  id?: number;
  uuid?: string;
  type_id: number;
  type?: EntryGroupTypeTable;
  entries?: EntryTable[];
}

export interface EntryGroup extends EntryGroupBase {
  id: number;
  uuid: string;
  type: EntryGroupType;
}

export interface EntryGroupWithMetadata extends EntryGroup {
  entries: Metadata[];
}

export interface EntryGroupCreate extends EntryGroupBase {
  type: string;
  entry_ids: number[];
}

// Main Entry models
export interface EntryBase {
  title: string;
  abstract: string;
  external_id?: string;
  location?: Point;
  version: number;
  latest_version_id?: number;
  is_partial: boolean;
  comment?: string;
  citation?: string;
  embargo: boolean;
  embargo_end?: string; // ISO 8601 datetime
  publication?: string; // ISO 8601 datetime
  lastUpdate?: string; // ISO 8601 datetime
}

export interface EntryTable {
  id?: number;
  uuid: string;
  title: string;
  abstract: string;
  external_id?: string;
  location?: string; // WKT string
  version: number;
  latest_version_id?: number;
  is_partial: boolean;
  comment?: string;
  citation?: string;
  embargo: boolean;
  embargo_end: string; // ISO 8601 datetime
  publication: string; // ISO 8601 datetime
  lastUpdate: string; // ISO 8601 datetime
  author_id?: number;
  license_id?: number;
  variable_id: number;
  datasource_id?: number;
  license?: LicenseTable;
  author?: PersonTable;
  coAuthors?: PersonTable[];
  variable?: VariableTable;
  keywords?: KeywordTable[];
  details?: DetailTable[];
  datasource?: DatasourceTable;
  groups?: EntryGroupTable[];
}

export interface EntryCreate extends EntryBase {
  license: LicenseCreate | number;
  variable: number;
  author: AuthorCreate | number;
  coAuthors?: (AuthorCreate | number)[];
  keywords?: number[];
  details?: DetailCreate[];
  datasource?: DatasourceCreate;
  groups?: (number | EntryGroupCreate)[];
}

export interface Metadata extends EntryBase {
  id: number;
  uuid: string;
  license?: License;
  variable: Variable;
  author: Author;
  coAuthors: CoAuthor[];
  keywords: Keyword[];
  details: Detail[];
  datasource?: Datasource;
}

// API Response types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: 'success' | 'error';
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

// Form types for creating/updating
export interface EntryFormData {
  title: string;
  abstract: string;
  external_id?: string;
  location?: [number, number]; // [longitude, latitude]
  version?: number;
  is_partial?: boolean;
  comment?: string;
  citation?: string;
  embargo?: boolean;
  embargo_end?: string;
  publication?: string;
  lastUpdate?: string;
  license_id?: number;
  variable_id: number;
  author_id?: number;
  co_author_ids?: number[];
  keyword_ids?: number[];
  datasource?: DatasourceCreate;
  group_ids?: number[];
}

// Search and filter types
export interface SearchFilters {
  title?: string;
  abstract?: string;
  author?: string;
  keywords?: string[];
  variable?: string;
  license?: string;
  date_from?: string;
  date_to?: string;
  location?: {
    lat: number;
    lng: number;
    radius: number; // in kilometers
  };
}

export interface SortOptions {
  field: 'title' | 'publication' | 'lastUpdate' | 'author' | 'variable';
  direction: 'asc' | 'desc';
}

// Export types
export interface ExportOptions {
  format: 'json' | 'xml' | 'csv';
  include_relationships?: boolean;
  filters?: SearchFilters;
  sort?: SortOptions;
}
