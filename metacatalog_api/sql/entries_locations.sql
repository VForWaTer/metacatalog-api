with geometries as (
    SELECT 
        entries.id,
        --CASE WHEN spatial_scales.extent IS NOT NULL THEN st_centroid(spatial_scales.extent) ELSE entries.location END AS center,
        CASE WHEN spatial_scales.extent IS NOT NULL THEN spatial_scales.extent ELSE entries.location END AS geom,
        --spatial_scales.extent,
        entries.title,
        variables.name AS variable
    FROM entries
    LEFT JOIN datasources ON datasources.id=datasource_id
    LEFT JOIN spatial_scales ON spatial_scales.id=datasources.spatial_scale_id
    LEFT JOIN variables ON variables.id=entries.variable_id
    WHERE ( spatial_scales.extent IS NOT NULL OR entries.location IS NOT NULL )
    {filter}
    {limit} {offset}
)
SELECT json_build_object(
    'type', 'FeatureCollection',
    'features', json_agg(st_AsGeoJSON(geometries.*)::json)
) FROM geometries;

