SELECT 
	entries.id,
	entries.uuid,
	entries.title,
	abstract,
	external_id,
	st_asewkt(location) as location,
	st_asewkt(location) as locationShape,
	version,
	row_to_json(licenses.*) as license,
	latest_version_id,
	is_partial,
	comment,
	citation,
	embargo,
	embargo_end,
	publication,
	"lastUpdate",
	(
		SELECT row_to_json(persons.*) from nm_persons_entries
		LEFT JOIN persons ON nm_persons_entries.person_id=persons.id
		WHERE nm_persons_entries.entry_id=entries.id AND relationship_type_id=1
	) AS author,
	(
		SELECT coalesce(json_agg(row_to_json(persons.*)), '[]'::json) from nm_persons_entries
		LEFT JOIN persons ON nm_persons_entries.person_id=persons.id
		LEFT JOIN person_roles ON person_roles.id=relationship_type_id
		WHERE nm_persons_entries.entry_id=entries.id AND person_roles.name='coAuthor'
		--ORDER BY "order" DESC
	) AS authors,
	(
		SELECT row_to_json(v.*) FROM (
			SELECT variables.id, variables.name, variables.symbol, column_names, 
			row_to_json(units.*) as unit, 
            json_build_object(
                'id', keywords.id,
                'uuid', keywords.uuid,
                'value', keywords.value,
                'path', keywords.full_path,
                'thesaurusName', row_to_json(thesaurus.*)                
            ) as keyword
			FROM variables
			LEFT JOIN units ON variables.unit_id=units.id
			LEFT JOIN keywords ON variables.keyword_id=keywords.id
            LEFT JOIN thesaurus ON keywords.thesaurus_id=thesaurus.id
			WHERE variables.id=entries.variable_id
		) as v
	) as variable,
	(
		SELECT row_to_json(d.*) FROM (
			SELECT datasources.id, datasources.path, datasources.variable_names, datasources.args::json, datasources.encoding,
			row_to_json(datasource_types.*) as type,
			case when spatial_scale_id is not null then 
            json_build_object(
				'id', spatial_scales.id, 
				'dimension_names', spatial_scales.dimension_names,
				'extent', st_asewkt(spatial_scales.extent),
				'resolution', spatial_scales.resolution,
				'resolution_str', (spatial_scales.resolution / 1000)::int || ' km',
				'support', spatial_scales.support,
				'support_str', (spatial_scales.support * spatial_scales.resolution / 1000)::int || ' km'
			) else null end as spatial_scale,
			case when temporal_scale_id is not NULL THEN 
            json_build_object(
				'id', temporal_scales.id,
				'dimension_names', temporal_scales.dimension_names,
				'extent', array[temporal_scales.observation_start, temporal_scales.observation_end],
				'resolution', temporal_scales.resolution,
				'support', temporal_scales.support
			) ELSE NULL END AS temporal_scale
			FROM datasources
			LEFT JOIN datasource_types ON datasource_types.id=datasources.type_id
			LEFT JOIN spatial_scales ON spatial_scales.id=spatial_scale_id
			LEFT JOIN temporal_scales ON temporal_scales.id=temporal_scale_id
			WHERE datasources.id=entries.datasource_id
		) as d
	) as datasource,
	(
		SELECT coalesce(json_agg(json_build_object(
			'id', id,
			'key', key,
			'stem', stem,
			'value', case when raw_value ? '__literal__' THEN raw_value->'__literal__' ELSE raw_value END
		)), '[]'::json)
		FROM details WHERE entry_id=entries.id
	) as details,
	(
		SELECT coalesce(json_agg(json_build_object(
			'id', keywords.id,
			'uuid', keywords.uuid,
			'value', keywords.value,
			'path', keywords.full_path,
			'thesaurusName', row_to_json(thesaurus.*)
		)), '[]'::json)
		FROM nm_keywords_entries 
		JOIN keywords on nm_keywords_entries.keyword_id=keywords.id AND nm_keywords_entries.entry_id=entries.id
		JOIN thesaurus ON keywords.thesaurus_id=thesaurus.id
	) as keywords
FROM entries
LEFT JOIN licenses ON licenses.id=entries.license_id
LEFT JOIN variables ON variables.id=entries.variable_id
{filter}
{limit} {offset};