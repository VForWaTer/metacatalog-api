from typing import Dict, Any
from datetime import datetime as dt
from datetime import timedelta as td
from uuid import UUID
import json

from dateparser import parse as dateparse

from metacatalog_api import models

def flatten_to_nested(flat_dict: Dict[str, str]) -> Dict[str, Any]:
    """
    Converts a flat dictionary with dot-separated keys into a nested dictionary.
    Numeric keys in dot-separated strings are treated as ordered list indices starting from 1,
    and contents within these lists are direct dictionaries without numeric keys.

    Args:
        flat_dict (Dict[str, str]): A dictionary where keys are structured as dot-separated strings.
    
    Returns:
        Dict[str, Any]: A nested dictionary representing the hierarchical structure.
    """
    nested_dict = {}

    for key, value in flat_dict.items():
        parts = key.split('.')
        current_level = nested_dict
        
        for i in range(len(parts) - 1):
            part = parts[i]

            # Check if the current part is an index and not the last part
            if part.isdigit() and (i > 0 and isinstance(current_level, list)):
                # Adjust for 1-based indexing
                index = int(part) - 1

                # Check if the list has enough elements
                while len(current_level) <= index:
                    current_level.append({})

                # Move the level to the current index
                current_level = current_level[index]
            elif i + 1 < len(parts) and parts[i + 1].isdigit():
                # If the next part is an index, ensure current level is a list
                if part not in current_level:
                    current_level[part] = []
                current_level = current_level[part]
            else:
                # Otherwise, handle as a dictionary
                if part not in current_level:
                    current_level[part] = {}
                current_level = current_level[part]

        # Set the final part's value
        last_part = parts[-1]
        if last_part.isdigit() and isinstance(current_level, list):
            # Adjust for 1-based indexing in list
            index = int(last_part) - 1
            while len(current_level) <= index:
                current_level.append(None)
            current_level[index] = value
        else:
            current_level[last_part] = value

    return nested_dict


def remove_empty_values(payload: dict) -> dict:
    """
    Removes empty values from a dictionary.
    Currently, None and '' are considered empty.
    """
    cleaned_payload = {}
    for k, v in payload.items():
        if v is None or v == '':
            continue
        elif isinstance(v, dict):
            child = remove_empty_values(v)
            if len(child) > 0:
                cleaned_payload[k] = child
        else:
            cleaned_payload[k] = v
    return cleaned_payload


def separate_string_list(string_list: str) -> list[str]:
    # separate and sanitize the string
    separated = [s.strip() for s in string_list.split(',')]
    sanitized = [chunk for chunk in separated if chunk != '']

    return sanitized

def dict_to_pg_payload(payload: dict) -> dict:
    """

    """
    insert_payload = {k: v for k, v in payload.items()}
    for k, v in insert_payload.items():
        # handle NULL
        if v is None or v == 'None':
            insert_payload[k] = 'NULL'
        # handle Array types
        elif isinstance(v, list) and all(isinstance(i, str) for i in v):
            insert_payload[k] = "'{" + ','.join(v) + "}'"
        # handle strings
        elif isinstance(v, str):
            insert_payload[k] = f"'{v}'"
        elif isinstance(v, dict) and len(v) == 0:
            insert_payload[k] = "'{}'::jsonb"
        elif isinstance(v, dict):
            insert_payload[k] = dict_to_pg_payload(v)
        elif isinstance(v, dt):
            insert_payload[k] = f"'{v.isoformat()}'"
        elif isinstance(v, UUID):
            insert_payload[k] = f"'{v}'"
    
    return insert_payload


def metadata_payload_to_model(payload: dict) -> models.MetadataPayload:
    """
    Converts a payload dictionary to a Metadata model.
    """
    # create the payload
    payload = flatten_to_nested(payload)
    
    # extract the license
    license = models.License(
        id=payload['license_id'],
        by_attribution=payload['license'].get('by_attribution'),
        share_alike=payload['license'].get('share_alike'), 
        commercial_use=payload['license'].get('commercial_use'), 
        short_title=payload['license']['short_title'],
        title=payload['license']['title'],
        summary=payload['license']['summary'],
        link=payload['license']['link'],
    )

    # extract the variable
    variable = models.Variable(**payload.pop('variable'))

    # extract the first author
    author = models.Author(**payload['authors'][0])
    authors = [models.Author(**a) for a in payload['authors'][1:]]

    # extract the location
         # extract the location
    if 'location' in payload:
        # Validate coordinates exist and are numeric
        loc = payload['location']
        if not all(k in loc for k in ('lon', 'lat')):
            raise ValueError("Location must contain 'lon' and 'lat' coordinates")
        try:
            lon = float(loc['lon'])
            lat = float(loc['lat'])
            # Basic coordinate validation
            if not (-180 <= lon <= 180 and -90 <= lat <= 90):
                raise ValueError("Invalid coordinate values")
        except (ValueError, TypeError):
            raise ValueError("Coordinates must be valid numbers")
        # Use parameterized format to prevent SQL injection
        location = f"POINT ({lon:f} {lat:f})"
    else:
        location = 'NULL'   

    meta = models.MetadataPayload(
        title=payload['title'],
        abstract=payload['abstract'],
        external_id=payload.get('external_id'),
        version=1,
        license=license,
        is_partial=False,
        comment=payload.get('comment'),
        location=location,
        variable=variable,
        citation=payload.get('citation'),
        embargo=False,
        embargo_end=dt.now() + td(days=2*365),
        publication=dt.now(),
        lastUpdate=dt.now(),
        author=author,
        authors=authors,
        details=[models.Detail(**d) for d in payload['details']],
    )

    return meta


def datasource_payload_to_model(payload: dict) -> models.DataSource:
    # create the payload
    payload = flatten_to_nested(payload)

    # remove all empty values
    payload = remove_empty_values(payload)

    # check if a temporal scale is provided
    if 'temporal_scale' in payload:
        temporal_scale = models.TemporalScale(
            resolution=payload['temporal_scale']['resolution'],
            extent=[
                dateparse(payload['temporal_scale']['observation_start']),
                dateparse(payload['temporal_scale']['observation_end'])
            ],
            support=1.0,
            dimension_names=separate_string_list(payload['temporal_scale']['dimension_names'])
        )
    else:
        temporal_scale = None
    
    # check if a spatial scale is provided
    if 'spatial_scale' in payload:
        spatial_scale = models.SpatialScale(
            resolution=payload['spatial_scale']['resolution'],
            extent=payload['spatial_scale']['extent'],
            support=1.0,
            dimension_names=separate_string_list(payload['spatial_scale']['dimension_names'])
        )
    else:
        spatial_scale = None

    # check if the datasource type is provided
    dtype = models.DataSourceType(**payload['type'])

    # handle the args
    args = payload.get('args', {})
    if not isinstance(args, dict):
        args = dict(__literal__=args)
        args = json.dumps(args)

    # finally create the datasource
    datasource = models.DataSource(
        path=payload['path'],
        type=dtype,
        variable_names=separate_string_list(payload['variable_names']),
        temporal_scale=temporal_scale,
        spatial_scale=spatial_scale,
        args=args,
        encoding=payload.get('encoding', 'utf-8')
    )

    return datasource
