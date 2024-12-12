-- create the new metacatalog_info table
CREATE TABLE {schema}.metacatalog_info
(
    db_version integer NOT NULL,
    min_py_version character varying(64) COLLATE pg_catalog."default",
    max_py_version character varying(64) COLLATE pg_catalog."default"
);

-- change the details table, make keys of type text
ALTER TABLE {schema}.details
    ALTER COLUMN key TYPE text COLLATE pg_catalog."default";

-- change the details table, make stems of type text
ALTER TABLE {schema}.details
    ALTER COLUMN stem TYPE text COLLATE pg_catalog."default";
ALTER TABLE IF EXISTS {schema}.details
    ALTER COLUMN stem DROP NOT NULL;

-- change the details, change the unique constraint from stem to key
ALTER TABLE IF EXISTS {schema}.details DROP CONSTRAINT IF EXISTS details_entry_id_stem_key;
ALTER TABLE IF EXISTS {schema}.details
    ADD CONSTRAINT details_entry_id_key UNIQUE (entry_id, key);
