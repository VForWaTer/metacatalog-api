with authors as (
	(
		SELECT persons.* as author FROM persons
		LEFT JOIN nm_persons_entries nm ON nm.person_id=persons.id
		LEFT JOIN person_roles ON nm.relationship_type_id=person_roles.id
		WHERE person_roles.name='author' AND nm.entry_id={entry_id}
	)
	UNION
	(
		SELECT persons.* as author FROM persons
		LEFT JOIN nm_persons_entries nm ON nm.person_id=persons.id
		LEFT JOIN person_roles ON nm.relationship_type_id=person_roles.id
		WHERE person_roles.name='coAuthor' AND nm.entry_id={entry_id}
		ORDER BY nm.order ASC
	)
	
)
SELECT row_to_json(authors.*) as author FROM authors;
