WITH filtered_persons AS (
    SELECT * FROM persons 
    WHERE is_organisation=true AND 
    organisation_name LIKE :prompt OR organisation_abbrev LIKE :prompt
    UNION
    SELECT * FROM persons
    WHERE is_organisation=false AND
    first_name || ' ' || last_name LIKE :prompt
)
SELECT * FROM filtered_persons
{limit} {offset}
;
