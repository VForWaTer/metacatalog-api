WITH inserted_unit AS (
    INSERT INTO units (name, symbol)
    VALUES ({unit[name]}, {unit[symbol]})
    ON CONFLICT (name) DO NOTHING
    RETURNING units.id
),
inserted_varaible AS (
    INSERT INTO variables (name, symbol, unit_id, column_names, keyword_id)
    VALUES (
        {variable[name]}, 
        {variable[symbol]},
        (
            SELECT id FROM inserted_unit
            UNION ALL
            SELECT units.id FROM units WHERE unit_name = {unit[name]} LIMIT 1
        )
       {variable[column_names]},
        {variable[keyword][id]}
    )
    ON CONFLICT (name) DO NOTHING
    RETURNING variables.id
),
inserted_license AS (
    INSERT INTO licenses (short_title, title, by_attribution, share_alike, commercial_use, summary, link)
    VALUES (
        {license[short_title]},
        {license[title]},
        {license[by_attribution]},
        {license[share_alike]},
        {license[commercial_use]},
        {license[summary]},
        {license[link]}
    )
    ON CONFLICT (short_title, title) DO NOTHING
    RETURNING licenses.id
)

INSERT INTO entries (uuid, title, abstract, external_id, location, version, latest_version_id, is_partial, comment, citation, license_id, variable_id, embargo, embargo_end, publication, "lastUpdate")
VALUES (
    gen_random_uuid(),
    {title},
    {abstract},
    {external_id},
    {location},
    {version},
    {latest_version_id},
    {entry_is_partial},
    {entry_comment},
    {entry_citation},
    (
        SELECT id FROM inserted_license
        UNION ALL
        SELECT licenses.id FROM licenses WHERE short_title = {license_short_title} LIMIT 1
    ),
    (
        SELECT id FROM inserted_variable
        UNION ALL
        SELECT variables.id FROM variables WHERE name = {variable_name} LIMIT 1
    ),
    {entry_embargo},
    {entry_embargo_end},
    {entry_publication},
    {entry_lastUpdate}
)
RETURNING entries.id;