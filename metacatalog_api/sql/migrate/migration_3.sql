-- change the entryGroup types
ALTER TABLE {schema}.entrygroup_types ALTER COLUMN name type TEXT NOT NULL;
ALTER TABLE {schema}.entrygroup_types ALTER COLUMN description type TEXT NOT NULL;

-- add new entry-group types
INSERT INTO {schema}.entrygroup_types VALUES (5, 'Dataset', 'A Dataset collects different self-contained entries (usually of different variables) that belong together. Other than composites, the single entries are self-contained and can be loaded individually.');
INSERT INTO {schema}.entrygroup_types VALUES (6, 'Site', 'A Site groups related entries, which have been collected at the same site. This can be used if the location or spatial-scale does not suffiently group the entries together.');
