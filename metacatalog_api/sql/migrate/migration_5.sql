-- Add orcid column to persons table for Zenodo integration
ALTER TABLE {schema}.persons ADD COLUMN orcid CHARACTER VARYING(19);

