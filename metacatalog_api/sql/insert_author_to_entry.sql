WITH inserted_person AS (
    INSERT INTO persons (uuid, is_organisation, first_name, last_name, organisation_name, organisation_abbrev, affiliation, attribution)
    VALUES (
        {uuid},
        {is_organisation},
        {first_name},
        {last_name},
        {organisation_name},
        {organisation_abbrev},
        {affiliation},
        {attribution}
    )
    ON CONFLICT (uuid) DO NOTHING
    RETURNING persons.id
)
INSERT INTO nm_persons_entries (person_id, entry_id, relationship_type_id, "order")
VALUES (
    (
        SELECT id FROM inserted_person
        UNION ALL
        SELECT persons.id FROM persons WHERE uuid = {uuid} LIMIT 1
    ),
    {entry_id},
    (
        SELECT id FROM person_roles WHERE name={role}
    ),
    {order}
)
;