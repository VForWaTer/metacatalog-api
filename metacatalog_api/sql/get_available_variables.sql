select 
	v.id,
	v.name,
	v.symbol,
	row_to_json(units.*) as unit,
	v.column_names,
	json_build_object(
		'id', keywords.id,
		'uuid', keywords.uuid,
		'value', keywords.value,
		'path', keywords.full_path,
		'thesaurusName', row_to_json(thesaurus.*)
	) as keyword
from variables v
LEFT JOIN units ON v.unit_id=units.id
LEFT JOIN keywords ON v.keyword_id=keywords.id
LEFT JOIN thesaurus ON keywords.thesaurus_id=thesaurus.id
WHERE EXISTS (SELECT id FROM entries WHERE variable_id=v.id)
{filter}
{limit} {offset}