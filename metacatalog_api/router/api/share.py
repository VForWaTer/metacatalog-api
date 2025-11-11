from pathlib import Path
import io
import zipfile
import json

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates

from metacatalog_api import core
from metacatalog_api.router.api.read import get_export_formats_list
from metacatalog_api.server import server

share_router = APIRouter()

templates = Jinja2Templates(directory=Path(__file__).parent / 'templates')


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


def create_share_package(entry_id: int, formats: list[str], include_data: bool = True) -> tuple[io.BytesIO, str]:
    """
    Create a shareable package with metadata and optionally data files.
    
    Returns:
        tuple: (zip_buffer, filename) where zip_buffer is a BytesIO object
    """
    # Get entry metadata
    entries = core.entries(ids=entry_id)
    if len(entries) == 0:
        raise HTTPException(status_code=404, detail=f"Entry of <ID={entry_id}> not found")
    
    entry = entries[0]
    
    # Create ZIP file in memory
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add metadata files in requested formats
        for format_name in formats:
            try:
                if format_name == 'json':
                    # JSON format
                    entry_dict = entry.model_dump(mode='json')
                    zip_file.writestr(
                        f"metadata/entry.json",
                        json.dumps(entry_dict, indent=2, default=str)
                    )
                elif format_name == 'xml':
                    # MetaCatalog XML
                    groups = core.groups(entry_id=entry_id)
                    template_content = templates.get_template("entry.xml").render(
                        entry=entry,
                        groups=groups,
                        path=server.app_prefix
                    )
                    zip_file.writestr(f"metadata/entry.xml", template_content)
                elif format_name in ['datacite', 'dublincore', 'rdf', 'zku']:
                    # Template-based formats
                    template_name = f"{format_name}.xml"
                    template_content = templates.get_template(template_name).render(entry=entry)
                    zip_file.writestr(f"metadata/entry_{format_name}.xml", template_content)
                elif format_name == 'schemaorg':
                    # Schema.org JSON-LD
                    template_content = templates.get_template("schemaorg.json").render(entry=entry)
                    zip_file.writestr(f"metadata/entry_schemaorg.json", template_content)
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


# This is the example for providing a new share provider
@share_router.get('/share/download/form')
def get_download_form(entry_id: int, request: Request):
    """
    Download Package
    """
    # Validate entry exists
    entries = core.entries(ids=entry_id)
    if len(entries) == 0:
        raise HTTPException(status_code=404, detail=f"Entry of <ID={entry_id}> not found")
    
    # Get available export formats dynamically
    export_formats = get_export_formats_list(request.app)
    format_options = [
        {"value": fmt['format'], "label": fmt['display_name']}
        for fmt in export_formats
    ]
    
    # Set default to first two formats, or json and datacite if available
    default_formats = []
    format_names = [fmt['format'] for fmt in export_formats]
    if 'json' in format_names:
        default_formats.append('json')
    if 'datacite' in format_names:
        default_formats.append('datacite')
    if len(default_formats) == 0 and len(format_names) > 0:
        default_formats = format_names[:2]  # First two formats as fallback
    
    return {
        "fields": [
            {
                "name": "metadata_formats",
                "type": "select",
                "label": "Metadata Formats",
                "required": True,
                "multiple": True,
                "options": format_options,
                "default": default_formats
            },
            {
                "name": "include_data",
                "type": "checkbox",
                "label": "Include Data Files",
                "default": True
            }
        ],
        "metadata_preview": False
    }


@share_router.post('/share/download/submit')
async def submit_download(entry_id: int, request: Request):
    """
    Submit download request and return package
    """
    # Parse request body
    try:
        body = await request.json()
        metadata_formats = body.get('metadata_formats', ['json', 'datacite'])
        include_data = body.get('include_data', True)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid request body. Expected JSON with 'metadata_formats' and 'include_data' fields.")
    
    # Validate formats against dynamically discovered export formats
    export_formats = get_export_formats_list(request.app)
    valid_formats = [fmt['format'] for fmt in export_formats]
    
    if not isinstance(metadata_formats, list) or not all(f in valid_formats for f in metadata_formats):
        format_names = ', '.join(valid_formats)
        raise HTTPException(
            status_code=400,
            detail=f"Invalid metadata_formats. Must be a list containing one or more of: {format_names}"
        )
    
    # Create package
    zip_buffer, filename = create_share_package(entry_id, metadata_formats, include_data)
    
    # Return ZIP file as streaming response
    # Note: zip_buffer is already a BytesIO object, we need to read its contents
    zip_data = zip_buffer.read()
    zip_buffer.close()
    
    return StreamingResponse(
        io.BytesIO(zip_data),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )

