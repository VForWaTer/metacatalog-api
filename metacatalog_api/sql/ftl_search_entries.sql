WITH filtered_entries AS (
	SELECT * FROM entries 
	{filter}
),
weights AS (
	SELECT 10 AS weight, 'title' as match, filtered_entries.id FROM filtered_entries 
    WHERE to_tsvector(title) @@ to_tsquery(:prompt) 
	UNION
	SELECT 8 AS weight, 'variable' as match, filtered_entries.id FROM filtered_entries LEFT JOIN variables on variables.id=filtered_entries.variable_id 
    WHERE to_tsvector(variables.name) @@ to_tsquery(:prompt)
	UNION
	SELECT 5 AS weight, 'abstract' as match, filtered_entries.id FROM filtered_entries 
    WHERE to_tsvector(abstract) @@ to_tsquery(:prompt)
	UNION 
	SELECT 1 AS weight, 'comment' as match, filtered_entries.id FROM filtered_entries 
    WHERE to_tsvector(comment) @@ to_tsquery(:prompt)
	UNION
	(
		SELECT 2 AS weight, 'coAuthors' as match, filtered_entries.id FROM filtered_entries
		LEFT JOIN nm_persons_entries nm ON nm.entry_id=filtered_entries.id
		LEFT JOIN persons on nm.person_id=persons.id
        WHERE to_tsvector(first_name || ' ' || last_name || ' ' || organisation_name) @@ to_tsquery(:prompt)
	)
	UNION 
	(
		SELECT 3 as weight, 'author' as match, filtered_entries.id FROM filtered_entries
		LEFT JOIN persons ON persons.id=filtered_entries.author_id
		WHERE to_tsvector(first_name || ' ' || last_name || ' ' || organisation_name || ' ' || organisation_abbrev) @@ to_tsquery(:prompt)
	)
	UNION
	(
		SELECT 6 as weight, 'detail' as match, filtered_entries.id FROM details
		LEFT JOIN filtered_entries ON details.entry_id=filtered_entries.id
		WHERE to_tsvector(details.key || ' ' || details.raw_value::text) @@ to_tsquery(:prompt)
		
	)
),
weight_sums as (
	SELECT SUM(weight) AS weight, array_agg(match) as matches, id FROM weights GROUP BY id ORDER by weight DESC
)
SELECT weight_sums.* as search_meta FROM weight_sums
ORDER BY weight_sums.weight DESC
{limit} {offset};