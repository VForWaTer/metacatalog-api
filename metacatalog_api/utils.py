from typing import Dict, Any
from datetime import datetime as dt
from datetime import timedelta as td
from uuid import UUID

from models import MetadataPayload, License, Author, Variable, Detail

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
        elif isinstance(v, dict):
            insert_payload[k] = dict_to_pg_payload(v)
        elif isinstance(v, dt):
            insert_payload[k] = f"'{v.isoformat()}'"
        elif isinstance(v, UUID):
            insert_payload[k] = f"'{v}'"
    
    return insert_payload


# {'title': 'Rewe', 'external_id': 'qwedwd', 'abstract': 'wqefdwfwe', 'variable_id': '8', 'variable.id': '8', 'authors.1.first_name': 'Mirko', 'authors.1.last_name': 'Mälicke ', 'authors.1.organisation_name': 'eem', 'authors.1.organisation_abbrev': 'emefm', 'authors.1.affiliation': '', 'authors.1.is_organisation': 'false', 'authors.1.id': '1730825268539', 'license_id': '8', 'license.by_attribution': 'true', 'license.share_alike': 'false', 'license.commercial_use': 'false', 'license.short_title': 'CC BY-NC 4.0', 'license.title': 'Creative Commons Attribution-NonCommerical 4.0 International', 'license.summary': 'You are free to: Share — copy and redistribute the material in any medium or format Adapt — remix, transform, and build upon the material. Under the following terms: Attribution — You must give appropriate credit, provide a link to the license, and indicate if changes were made. You may do so in any reasonable manner, but not in any way that suggests the licensor endorses you or your use.  NonCommercial — You may not use the material for commercial purposes.', 'license.link': 'https://creativecommons.org/licenses/by-nc/4.0/legalcode.txt ', 'details.1.key': 'foo', 'details.1.stem': 'foo', 'details.1.value': 'Bar', 'details.2.key': 'Testset', 'details.2.stem': 'Testset', 'details.2.value': 'false'}
def metadata_payload_to_model(payload: dict) -> MetadataPayload:
    """
    Converts a payload dictionary to a Metadata model.
    """
    # create the payload
    payload = flatten_to_nested(payload)
    
    # extract the license
    license = License(
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
    variable = Variable(**payload.pop('variable'))

    # extract the first author
    author = Author(**payload['authors'][0])
    authors = [Author(**a) for a in payload['authors'][1:]]

    meta = MetadataPayload(
        title=payload['title'],
        abstract=payload['abstract'],
        external_id=payload.get('external_id'),
        version=1,
        license=license,
        is_partial=False,
        comment=payload.get('comment'),
        location=payload.get('location'),
        variable=variable,
        citation=payload.get('citation'),
        embargo=False,
        embargo_end=dt.now() + td(days=2*365),
        publication=dt.now(),
        lastUpdate=dt.now(),
        author=author,
        authors=authors,
        details=[Detail(**d) for d in payload['details']],
    )

    return meta
