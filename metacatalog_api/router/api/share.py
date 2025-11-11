import io
import json
import zipfile

from fastapi import APIRouter, Request


from metacatalog_api import core
from metacatalog_api.router.api.export import render_export


share_router = APIRouter()


@share_router.get('/share-providers')
def get_share_providers(request: Request):
    """
    Get all available share providers by scanning FastAPI routes
    """
    app = request.app
    
    providers = {}
    
    # First pass: collect all share routes
    for route in app.routes:
        if hasattr(route, 'path') and route.path.startswith('/share/'):
            path_parts = route.path.split('/')
            if len(path_parts) >= 3 and path_parts[1] == 'share':
                provider_name = path_parts[2]  # Gets 'download', 'zenodo', etc.
                
                if provider_name not in providers:
                    providers[provider_name] = {
                        'provider': provider_name,
                        'form_endpoint': None,
                        'submit_endpoint': None,
                        'display_name': provider_name.title()
                    }
                
                # Check if this is a form or submit route
                if len(path_parts) >= 4:
                    route_type = path_parts[3]  # 'form' or 'submit'
                    if route_type == 'form':
                        providers[provider_name]['form_endpoint'] = route.path
                        # Extract display name from docstring
                        if hasattr(route, 'endpoint') and hasattr(route.endpoint, '__doc__') and route.endpoint.__doc__:
                            docstring = route.endpoint.__doc__.strip()
                            first_line = docstring.split('\n')[0].strip()
                            if first_line:
                                providers[provider_name]['display_name'] = first_line
                    elif route_type == 'submit':
                        providers[provider_name]['submit_endpoint'] = route.path
    
    # Filter to only include providers with both form and submit endpoints
    valid_providers = [
        provider for provider in providers.values()
        if provider['form_endpoint'] and provider['submit_endpoint']
    ]
    
    return {"share_providers": valid_providers}


def create_share_package(request: Request, entry_id: int, formats: list[str], include_data: bool = True) -> tuple[io.BytesIO, str]:
    """
    Create a shareable package with metadata and optionally data files.
    
    Returns:
        tuple: (zip_buffer, filename) where zip_buffer is a BytesIO object
    """
    app = request.app
    
    # Create ZIP file in memory
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add metadata files in requested formats using dynamic export system
        for format_name in formats:
            try:
                content, filename = render_export(app, entry_id, format_name, request)
                zip_file.writestr(f"metadata/{filename}", content)
            except Exception as e:
                # Skip formats that fail, but continue with others
                continue
        
        # Add data files if requested
        if include_data:
            # Use core function to get data file info
            data_info = core.get_entry_data_file(entry_id)
            
            if data_info['error']:
                # Create error manifest
                manifest = {
                    "type": "error",
                    "error": data_info['error'],
                    "description": "Data file could not be included in package"
                }
                zip_file.writestr("data/manifest.json", json.dumps(manifest, indent=2))
            elif data_info['is_stream']:
                # Internal table - stream data to ZIP
                csv_content = ""
                for chunk in data_info['stream_generator']():
                    csv_content += chunk
                zip_file.writestr(f"data/{data_info['filename']}", csv_content)
            elif data_info['file_path']:
                # File-based datasource - add file to ZIP
                zip_file.write(str(data_info['file_path']), f"data/{data_info['filename']}")
            else:
                # External or unsupported - create manifest
                entries = core.entries(ids=entry_id)
                if entries and entries[0].datasource:
                    datasource = entries[0].datasource
                    if datasource.type.name == "external":
                        manifest = {
                            "type": "external",
                            "url": datasource.path,
                            "description": "External datasource - data not included in package"
                        }
                    else:
                        manifest = {
                            "type": datasource.type.name if datasource.type else "unknown",
                            "path": datasource.path,
                            "status": "unsupported",
                            "description": f"Datasource type '{datasource.type.name if datasource.type else 'unknown'}' is not supported for packaging"
                        }
                    zip_file.writestr("data/manifest.json", json.dumps(manifest, indent=2))
    
    zip_buffer.seek(0)
    filename = f"entry_{entry_id}_package.zip"
    
    return zip_buffer, filename

