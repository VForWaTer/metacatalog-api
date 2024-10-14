from typing import Dict, Any

def flatten_to_nested(flat_dict: Dict[str, str]) -> Dict[str, Any]:
    """
    Converts a flat dictionary with dot-separated keys into a nested dictionary.
    Args:
        flat_dict (Dict[str, str]): A dictionary where keys are dot-separated strings representing the hierarchy.
    Returns:
        Dict[str, Any]: A nested dictionary constructed from the flat dictionary.

    """
    nested_dict = {}
    
    for key, value in flat_dict.items():
        parts = key.split('.')
        current_level = nested_dict
        
        for part in parts[:-1]:  # Navigate to the second-to-last part
            if part not in current_level:
                current_level[part] = {}
            current_level = current_level[part]
        
        # Set the value in the last part
        current_level[parts[-1]] = value

    return nested_dict
