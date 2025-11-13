import io
import json

from fastapi import Request, HTTPException
from fastapi.responses import StreamingResponse

from metacatalog_api import core
from metacatalog_api.router.api.share import share_router, create_share_package
from metacatalog_api.router.api.read import get_export_formats_list


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
    except (json.JSONDecodeError, ValueError, TypeError, KeyError) as e:
        raise HTTPException(status_code=400, detail="Invalid request body. Expected JSON with 'metadata_formats' and 'include_data' fields.") from e
    
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
    zip_buffer, filename = create_share_package(request, entry_id, metadata_formats, include_data)
    
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
