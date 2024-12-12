-- add a new column to the entries table
ALTER TABLE IF EXISTS {schema}.entries
    ADD COLUMN IF NOT EXISTS author_id integer;
ALTER TABLE IF EXISTS {schema}.entries
    ADD CONSTRAINT entries_author_id_fkey FOREIGN KEY (author_id)
    REFERENCES {schema}.persons (id) MATCH SIMPLE
    ON UPDATE CASCADE
    ON DELETE SET NULL;

-- get the first author of every entry and set as the new author_id
UPDATE {schema}.entries 
SET author_id=ids.person_id 
FROM (
	SELECT entry_id, person_id FROM {schema}.nm_persons_entries
	WHERE relationship_type_id=1
) AS ids
WHERE ids.entry_id=entries.id;
DELETE FROM {schema}.nm_persons_entries WHERE relationship_type_id=1;

-- make datasource.args to JSONB
ALTER TABLE IF EXISTS {schema}.datasources
    ALTER COLUMN args TYPE JSONB USING args::jsonb;

-- make datatype_id not null
ALTER TABLE IF EXISTS {schema}.datasources
    ALTER COLUMN datatype_id DROP NOT NULL;

