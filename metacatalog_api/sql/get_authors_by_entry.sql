(
	SELECT persons.*
	FROM nm_persons_entries
	JOIN person_roles ON person_roles.id=relationship_type_id
	JOIN persons ON persons.id=nm_persons_entries.person_id
	WHERE person_roles.name = 'author'
	AND entry_id={entry_id}
	ORDER by "order" ASC
)
UNION
(
	SELECT persons.*
	FROM nm_persons_entries
	JOIN person_roles ON person_roles.id=relationship_type_id
	JOIN persons ON persons.id=nm_persons_entries.person_id
	WHERE person_roles.name = 'coAuthor'
	AND entry_id={entry_id}
	ORDER by "order" ASC
)


