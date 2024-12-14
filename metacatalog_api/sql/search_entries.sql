WITH filtered_entries AS (
	SELECT * FROM entries 
	{filter}
),
weights AS (
	SELECT 10 AS weight, 'title' as match, filtered_entries.id FROM filtered_entries WHERE title LIKE :prompt 
	UNION
	SELECT 8 AS weight, 'variable' as match, filtered_entries.id FROM filtered_entries LEFT JOIN variables on variables.id=filtered_entries.variable_id WHERE variables.name LIKE :prompt
	UNION
	SELECT 5 AS weight, 'abstract' as match, filtered_entries.id FROM filtered_entries WHERE abstract LIKE :prompt
	UNION 
	SELECT 1 AS weight, 'comment' as match, filtered_entries.id FROM filtered_entries WHERE comment LIKE :prompt
	UNION
	(
		SELECT 2 AS weight, 'coAuthors' as match, filtered_entries.id FROM filtered_entries
		LEFT JOIN nm_persons_entries nm ON nm.entry_id=filtered_entries.id
		LEFT JOIN persons on nm.person_id=persons.id
		WHERE first_name LIKE :prompt OR last_name LIKE :prompt or organisation_name LIKE :prompt
	)
	UNION 
	(
		SELECT 3 as weight, 'author' as match, filtered_entries.id FROM filtered_entries
		LEFT JOIN persons ON persons.id=filtered_entries.author_id
		WHERE first_name LIKE :prompt OR last_name LIKE :prompt or organisation_name LIKE :prompt
	)
	UNION
	(
		SELECT 6 as weight, 'detail' as match, filtered_entries.id FROM details
		LEFT JOIN filtered_entries ON details.entry_id=filtered_entries.id
		WHERE details.key LIKE :prompt OR details.raw_value::text LIKE :prompt
		
	)
),
weight_sums as (
	SELECT SUM(weight) AS weight, array_agg(match) as matches, id FROM weights GROUP BY id ORDER by weight DESC
)
SELECT weight_sums.* as search_meta FROM weight_sums
ORDER BY weight_sums.weight DESC
{limit} {offset};