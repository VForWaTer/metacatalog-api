WITH inserted_type AS (
	INSERT INTO datasource_types (name, title, description)
	VALUES ({type[name]}, {type[title]}, {type[description]})
	ON CONFLICT (name) DO NOTHING
	RETURNING datasource_types.id
),
-- inserted_datatype AS (
-- 	INSERT INTO datatypes (parent_id, name, title, description)
-- 	VALUES (1, 'blob', 'BLOB data', 'Non existent datatype')
-- 	ON CONFLICT (name) DO NOTHING
-- 	RETURNING datatypes.id
-- ),
inserted_temporal_scale AS (
	INSERT INTO temporal_scales (resolution, observation_start, observation_end, support, dimension_names)
	SELECT  
        {temporal_scale[resolution]},
        {temporal_scale[observation_start]},
        {temporal_scale[observation_end]},
        {temporal_scale[support]},
        {temporal_scale[dimension_names]}
	WHERE {temporal_scale[resolution]} IS NOT NULL 
        AND {temporal_scale[observation_start]} IS NOT NULL 
        AND {temporal_scale[observation_end]} IS NOT NULL 
        AND {temporal_scale[support]} IS NOT NULL 
        AND {temporal_scale[dimension_names]} IS NOT NULL
	ON CONFLICT (id) DO NOTHING
	RETURNING temporal_scales.id
),
inserted_spatial_scale AS (
	INSERT INTO spatial_scales (resolution, extent, support, dimension_names)
	SELECT 
        {spatial_scale[resolution]},
        {spatial_scale[extent]},
        {spatial_scale[support]},
        {spatial_scale[dimension_names]}
	WHERE {spatial_scale[resolution]} IS NOT NULL 
        AND {spatial_scale[extent]} IS NOT NULL
        AND {spatial_scale[support]} IS NOT NULL
        AND {spatial_scale[dimension_names]} IS NOT NULL
	ON CONFLICT (id) DO NOTHING
	RETURNING spatial_scales.id
),
inserted_datasource AS (
    INSERT INTO datasources (type_id, datatype_id, encoding, path, data_names, variable_names, args, temporal_scale_id, spatial_scale_id, creation, "lastUpdate")
    VALUES (
        (
            SELECT id FROM inserted_type
            UNION ALL
            SELECT datasource_types.id FROM datasource_types WHERE name={type[name]} LIMIT 1

        ),
        -- we just choose something here
        11,
        {encoding},
        {path},
        NULL, -- data_names are always NULL
        {variable_names},
        {args},
        CASE WHEN (SELECT id FROM inserted_temporal_scale) IS NOT NULL 
            THEN (SELECT id FROM inserted_temporal_scale)
            ELSE NULL
        END,
        CASE WHEN (SELECT id FROM inserted_spatial_scale) IS NOT NULL
            THEN (SELECT id FROM inserted_spatial_scale)
            ELSE NULL
        END,
        NOW(),
        NOW()
    )
    RETURNING datasources.id
)
UPDATE entries SET datasource_id=(SELECT id FROM inserted_datasource)
WHERE entries.id={entry_id}
RETURNING entries.datasource_id;

