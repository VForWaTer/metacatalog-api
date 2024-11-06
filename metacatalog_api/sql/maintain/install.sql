-- CREATE EXTENSION postgis;

-- UNITS
CREATE SEQUENCE IF NOT EXISTS public.units_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

CREATE TABLE IF NOT EXISTS {schema}.units
(
    id integer NOT NULL DEFAULT nextval('units_id_seq'::regclass),
    name character varying(64) COLLATE pg_catalog."default" NOT NULL,
    symbol character varying(12) COLLATE pg_catalog."default" NOT NULL,
    si character varying COLLATE pg_catalog."default",
    CONSTRAINT units_pkey PRIMARY KEY (id),
    CONSTRAINT units_name_key UNIQUE (name)
);

ALTER SEQUENCE units_id_seq OWNED BY units.id;

-- THESAURUS
CREATE SEQUENCE IF NOT EXISTS public.thesaurus_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

CREATE TABLE IF NOT EXISTS {schema}.thesaurus
(
    id integer NOT NULL DEFAULT nextval('thesaurus_id_seq'::regclass),
    uuid character varying(64) COLLATE pg_catalog."default" NOT NULL,
    name character varying(1024) COLLATE pg_catalog."default" NOT NULL,
    title character varying COLLATE pg_catalog."default" NOT NULL,
    organisation character varying COLLATE pg_catalog."default" NOT NULL,
    description character varying COLLATE pg_catalog."default",
    url character varying COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT thesaurus_pkey PRIMARY KEY (id),
    CONSTRAINT thesaurus_name_key UNIQUE (name),
    CONSTRAINT thesaurus_uuid_key UNIQUE (uuid)
);

ALTER SEQUENCE thesaurus_id_seq OWNED BY thesaurus.id;

-- KEYWORDS
CREATE SEQUENCE IF NOT EXISTS public.keywords_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

CREATE TABLE IF NOT EXISTS {schema}.keywords
(
    id integer NOT NULL DEFAULT nextval('keywords_id_seq'::regclass),
    uuid character varying(64) COLLATE pg_catalog."default",
    parent_id integer,
    value character varying(1024) COLLATE pg_catalog."default" NOT NULL,
    full_path character varying COLLATE pg_catalog."default",
    thesaurus_id integer,
    CONSTRAINT keywords_pkey PRIMARY KEY (id),
    CONSTRAINT keywords_uuid_key UNIQUE (uuid),
    CONSTRAINT keywords_parent_id_fkey FOREIGN KEY (parent_id)
        REFERENCES {schema}.keywords (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT keywords_thesaurus_id_fkey FOREIGN KEY (thesaurus_id)
        REFERENCES {schema}.thesaurus (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);

ALTER SEQUENCE keywords_id_seq OWNED BY keywords.id;

-- VARIABLES
CREATE SEQUENCE IF NOT EXISTS public.variables_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

CREATE TABLE IF NOT EXISTS {schema}.variables
(
    id integer NOT NULL DEFAULT nextval('variables_id_seq'::regclass),
    name character varying(64) COLLATE pg_catalog."default" NOT NULL,
    symbol character varying(12) COLLATE pg_catalog."default" NOT NULL,
    column_names character varying(128)[] COLLATE pg_catalog."default" NOT NULL,
    unit_id integer NOT NULL,
    keyword_id integer,
    CONSTRAINT variables_pkey PRIMARY KEY (id),
    CONSTRAINT variables_name_key UNIQUE (name),
    CONSTRAINT variables_keyword_id_fkey FOREIGN KEY (keyword_id)
        REFERENCES {schema}.keywords (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT variables_unit_id_fkey FOREIGN KEY (unit_id)
        REFERENCES {schema}.units (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);

ALTER SEQUENCE variables_id_seq OWNED BY variables.id;

-- LICENSES
CREATE SEQUENCE IF NOT EXISTS public.licenses_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

CREATE TABLE IF NOT EXISTS {schema}.licenses
(
    id integer NOT NULL DEFAULT nextval('licenses_id_seq'::regclass),
    short_title character varying(40) COLLATE pg_catalog."default" NOT NULL,
    title character varying COLLATE pg_catalog."default" NOT NULL,
    summary character varying COLLATE pg_catalog."default",
    full_text character varying COLLATE pg_catalog."default",
    link character varying COLLATE pg_catalog."default",
    by_attribution boolean NOT NULL,
    share_alike boolean NOT NULL,
    commercial_use boolean NOT NULL,
    CONSTRAINT licenses_pkey PRIMARY KEY (id),
    CONSTRAINT license_name_key UNIQUE (short_title),
    CONSTRAINT license_title_key UNIQUE (title),
    CONSTRAINT licenses_check CHECK (NOT (full_text IS NULL AND link IS NULL))
);

ALTER SEQUENCE licenses_id_seq OWNED BY licenses.id;


-- DATATYPES
CREATE SEQUENCE IF NOT EXISTS public.datatypes_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

CREATE TABLE IF NOT EXISTS {schema}.datatypes
(
    id integer NOT NULL DEFAULT nextval('datatypes_id_seq'::regclass),
    parent_id integer,
    name character varying(64) COLLATE pg_catalog."default" NOT NULL,
    title character varying COLLATE pg_catalog."default" NOT NULL,
    description character varying COLLATE pg_catalog."default",
    CONSTRAINT datatypes_pkey PRIMARY KEY (id),
    CONSTRAINT datatypes_name_key UNIQUE (name),
    CONSTRAINT datatypes_parent_id_fkey FOREIGN KEY (parent_id)
        REFERENCES {schema}.datatypes (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);

ALTER SEQUENCE datatypes_id_seq OWNED BY datatypes.id;


-- DATASOURCE_TYPES
CREATE SEQUENCE IF NOT EXISTS public.datasource_types_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

CREATE TABLE IF NOT EXISTS {schema}.datasource_types
(
    id integer NOT NULL DEFAULT nextval('datasource_types_id_seq'::regclass),
    name character varying(64) COLLATE pg_catalog."default" NOT NULL,
    title character varying COLLATE pg_catalog."default" NOT NULL,
    description character varying COLLATE pg_catalog."default",
    CONSTRAINT datasource_types_pkey PRIMARY KEY (id),
    CONSTRAINT datasource_types_name_key UNIQUE (name)
);

ALTER SEQUENCE datasource_types_id_seq OWNED BY datasource_types.id;


-- TEMPORAL_SCALES
CREATE SEQUENCE IF NOT EXISTS public.temporal_scales_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

CREATE TABLE IF NOT EXISTS {schema}.temporal_scales
(
    id integer NOT NULL DEFAULT nextval('temporal_scales_id_seq'::regclass),
    resolution character varying COLLATE pg_catalog."default" NOT NULL,
    observation_start timestamp without time zone NOT NULL,
    observation_end timestamp without time zone NOT NULL,
    support numeric NOT NULL,
    dimension_names character varying(32)[] COLLATE pg_catalog."default",
    CONSTRAINT temporal_scales_pkey PRIMARY KEY (id),
    CONSTRAINT temporal_scales_support_check CHECK (support >= 0::numeric)
);
 
ALTER SEQUENCE temporal_scales_id_seq OWNED BY temporal_scales.id;


-- SPATIAL_SCALES
CREATE SEQUENCE IF NOT EXISTS public.spatial_scales_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

CREATE TABLE IF NOT EXISTS {schema}.spatial_scales
(
    id integer NOT NULL DEFAULT nextval('spatial_scales_id_seq'::regclass),
    resolution integer NOT NULL,
    extent geometry(Polygon,4326) NOT NULL,
    support numeric NOT NULL,
    dimension_names character varying(32)[] COLLATE pg_catalog."default",
    CONSTRAINT spatial_scales_pkey PRIMARY KEY (id),
    CONSTRAINT spatial_scales_support_check CHECK (support >= 0::numeric)
);

ALTER SEQUENCE spatial_scales_id_seq OWNED BY spatial_scales.id;

-- DATASOURCES
CREATE SEQUENCE IF NOT EXISTS public.datasources_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

CREATE TABLE IF NOT EXISTS {schema}.datasources
(
    id integer NOT NULL DEFAULT nextval('datasources_id_seq'::regclass),
    type_id integer NOT NULL,
    datatype_id integer NOT NULL,
    encoding character varying(64) COLLATE pg_catalog."default",
    path character varying COLLATE pg_catalog."default" NOT NULL,
    data_names character varying(128)[] COLLATE pg_catalog."default",
    variable_names character varying(128)[] COLLATE pg_catalog."default",
    args character varying COLLATE pg_catalog."default",
    temporal_scale_id integer,
    spatial_scale_id integer,
    creation timestamp without time zone,
    "lastUpdate" timestamp without time zone,
    CONSTRAINT datasources_pkey PRIMARY KEY (id),
    CONSTRAINT datasources_datatype_id_fkey FOREIGN KEY (datatype_id)
        REFERENCES {schema}.datatypes (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT datasources_spatial_scale_id_fkey FOREIGN KEY (spatial_scale_id)
        REFERENCES {schema}.spatial_scales (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT datasources_temporal_scale_id_fkey FOREIGN KEY (temporal_scale_id)
        REFERENCES {schema}.temporal_scales (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT datasources_type_id_fkey FOREIGN KEY (type_id)
        REFERENCES {schema}.datasource_types (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);

ALTER SEQUENCE datasources_id_seq OWNED BY datasources.id;


-- PERSON_ROLES
CREATE SEQUENCE IF NOT EXISTS public.person_roles_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

CREATE TABLE IF NOT EXISTS {schema}.person_roles
(
    id integer NOT NULL DEFAULT nextval('person_roles_id_seq'::regclass),
    name character varying(64) COLLATE pg_catalog."default" NOT NULL,
    description character varying COLLATE pg_catalog."default",
    CONSTRAINT person_roles_pkey PRIMARY KEY (id),
    CONSTRAINT person_roles_name_key UNIQUE (name)
);

ALTER SEQUENCE person_roles_id_seq OWNED BY person_roles.id;

-- PERSONS
CREATE SEQUENCE IF NOT EXISTS public.persons_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

CREATE TABLE IF NOT EXISTS {schema}.persons
(
    id integer NOT NULL DEFAULT nextval('persons_id_seq'::regclass),
    uuid character varying(36) COLLATE pg_catalog."default" NOT NULL,
    is_organisation boolean,
    first_name character varying(128) COLLATE pg_catalog."default",
    last_name character varying(128) COLLATE pg_catalog."default",
    organisation_name character varying(1024) COLLATE pg_catalog."default",
    organisation_abbrev character varying(64) COLLATE pg_catalog."default",
    affiliation character varying(1024) COLLATE pg_catalog."default",
    attribution character varying(1024) COLLATE pg_catalog."default",
    CONSTRAINT persons_pkey PRIMARY KEY (id),
    CONSTRAINT persons_check CHECK (NOT (last_name IS NULL AND organisation_name IS NULL)),
    CONSTRAINT persons_uuid_key UNIQUE (uuid)
);

ALTER SEQUENCE persons_id_seq OWNED BY persons.id;

-- ENTRIES
CREATE SEQUENCE IF NOT EXISTS public.entries_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

CREATE TABLE IF NOT EXISTS {schema}.entries
(
    id integer NOT NULL DEFAULT nextval('entries_id_seq'::regclass),
    uuid character varying(36) COLLATE pg_catalog."default" NOT NULL,
    title character varying(512) COLLATE pg_catalog."default" NOT NULL,
    abstract character varying COLLATE pg_catalog."default",
    external_id character varying COLLATE pg_catalog."default",
    location geometry(Point,4326),
    version integer NOT NULL,
    latest_version_id integer,
    is_partial boolean NOT NULL,
    comment character varying COLLATE pg_catalog."default",
    citation character varying(2048) COLLATE pg_catalog."default",
    license_id integer,
    variable_id integer NOT NULL,
    datasource_id integer,
    embargo boolean NOT NULL,
    embargo_end timestamp without time zone,
    publication timestamp without time zone,
    "lastUpdate" timestamp without time zone,
    CONSTRAINT entries_pkey PRIMARY KEY (id),
    CONSTRAINT entries_datasource_id_fkey FOREIGN KEY (datasource_id)
        REFERENCES {schema}.datasources (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT entries_latest_version_id_fkey FOREIGN KEY (latest_version_id)
        REFERENCES {schema}.entries (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT entries_license_id_fkey FOREIGN KEY (license_id)
        REFERENCES {schema}.licenses (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT entries_variable_id_fkey FOREIGN KEY (variable_id)
        REFERENCES {schema}.variables (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);

ALTER SEQUENCE entries_id_seq OWNED BY entries.id;

-- DETAILS
CREATE SEQUENCE IF NOT EXISTS public.details_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

CREATE TABLE IF NOT EXISTS {schema}.details
(
    id integer NOT NULL DEFAULT nextval('details_id_seq'::regclass),
    entry_id integer,
    key character varying(60) COLLATE pg_catalog."default" NOT NULL,
    stem character varying(20) COLLATE pg_catalog."default" NOT NULL,
    title character varying COLLATE pg_catalog."default",
    raw_value jsonb NOT NULL,
    description character varying COLLATE pg_catalog."default",
    thesaurus_id integer,
    CONSTRAINT details_pkey PRIMARY KEY (id),
    CONSTRAINT details_entry_id_stem_key UNIQUE (entry_id, stem),
    CONSTRAINT details_entry_id_fkey FOREIGN KEY (entry_id)
        REFERENCES {schema}.entries (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT details_thesaurus_id_fkey FOREIGN KEY (thesaurus_id)
        REFERENCES {schema}.thesaurus (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);

ALTER SEQUENCE details_id_seq OWNED BY details.id;

-- ENTRYGROUP_TYPES
CREATE SEQUENCE IF NOT EXISTS public.entrygroup_types_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

CREATE TABLE IF NOT EXISTS {schema}.entrygroup_types
(
    id integer NOT NULL DEFAULT nextval('entrygroup_types_id_seq'::regclass),
    name character varying(40) COLLATE pg_catalog."default" NOT NULL,
    description character varying COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT entrygroup_types_pkey PRIMARY KEY (id)
);

ALTER SEQUENCE entrygroup_types_id_seq OWNED BY entrygroup_types.id;

-- ENTRYGROUPS
CREATE SEQUENCE IF NOT EXISTS public.entrygroups_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

CREATE TABLE IF NOT EXISTS {schema}.entrygroups
(
    id integer NOT NULL DEFAULT nextval('entrygroups_id_seq'::regclass),
    uuid character varying(36) COLLATE pg_catalog."default" NOT NULL,
    type_id integer NOT NULL,
    title character varying(250) COLLATE pg_catalog."default",
    description character varying COLLATE pg_catalog."default",
    publication timestamp without time zone,
    "lastUpdate" timestamp without time zone,
    CONSTRAINT entrygroups_pkey PRIMARY KEY (id),
    CONSTRAINT entrygroups_type_id_fkey FOREIGN KEY (type_id)
        REFERENCES {schema}.entrygroup_types (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);

ALTER SEQUENCE entrygroups_id_seq OWNED BY entrygroups.id;


-- ASSOCIATION TABLES
CREATE TABLE IF NOT EXISTS {schema}.nm_keywords_entries
(
    keyword_id integer NOT NULL,
    entry_id integer NOT NULL,
    CONSTRAINT nm_keywords_entries_pkey PRIMARY KEY (keyword_id, entry_id),
    CONSTRAINT nm_keywords_entries_entry_id_fkey FOREIGN KEY (entry_id)
        REFERENCES {schema}.entries (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT nm_keywords_entries_keyword_id_fkey FOREIGN KEY (keyword_id)
        REFERENCES {schema}.keywords (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);

CREATE TABLE IF NOT EXISTS {schema}.nm_persons_entries
(
    person_id integer NOT NULL,
    entry_id integer NOT NULL,
    relationship_type_id integer NOT NULL,
    "order" integer NOT NULL,
    CONSTRAINT nm_persons_entries_pkey PRIMARY KEY (person_id, entry_id),
    CONSTRAINT nm_persons_entries_entry_id_fkey FOREIGN KEY (entry_id)
        REFERENCES {schema}.entries (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT nm_persons_entries_person_id_fkey FOREIGN KEY (person_id)
        REFERENCES {schema}.persons (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT nm_persons_entries_relationship_type_id_fkey FOREIGN KEY (relationship_type_id)
        REFERENCES {schema}.person_roles (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);

CREATE TABLE IF NOT EXISTS {schema}.nm_entrygroups
(
    entry_id integer NOT NULL,
    group_id integer NOT NULL,
    CONSTRAINT nm_entrygroups_pkey PRIMARY KEY (entry_id, group_id),
    CONSTRAINT nm_entrygroups_entry_id_fkey FOREIGN KEY (entry_id)
        REFERENCES {schema}.entries (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT nm_entrygroups_group_id_fkey FOREIGN KEY (group_id)
        REFERENCES {schema}.entrygroups (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);
