WITH weights AS (
	SELECT 10 AS weight, 'title' as match, entries.id FROM entries WHERE title LIKE '%{prompt}%' 
	UNION
	SELECT 8 AS weight, 'variable' as match, entries.id FROM entries LEFT JOIN variables on variables.id=entries.variable_id WHERE variables.name LIKE '%{prompt}%'
	UNION
	SELECT 5 AS weight, 'abstract' as match, entries.id FROM entries WHERE abstract LIKE '%{prompt}%'
	UNION 
	SELECT 1 AS weight, 'comment' as match, entries.id FROM entries WHERE comment LIKE '%{prompt}%'
	UNION
	(
		SELECT 2 AS weight, 'author' as match, entries.id FROM entries
		LEFT JOIN nm_persons_entries nm ON nm.entry_id=entries.id
		LEFT JOIN persons on nm.person_id=persons.id
		WHERE first_name LIKE '%{prompt}%' OR last_name LIKE '%{prompt}%' or organisation_name LIKE '%{prompt}%'
	)

),
weight_sums as (
	SELECT SUM(weight) AS weight, array_agg(match) as matches, id FROM weights GROUP BY id ORDER by weight DESC
)
SELECT row_to_json(weight_sums.*) as search_meta FROM weight_sums
ORDER BY weight_sums.weight DESC
{limit} {offset};