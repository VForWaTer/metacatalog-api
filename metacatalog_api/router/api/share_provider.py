import io
import json
import zipfile
from pathlib import Path

import httpx
from fastapi import Request, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates
from jinja2 import TemplateError

from metacatalog_api import core, models
from metacatalog_api.router.api.share import share_router, create_share_package
from metacatalog_api.router.api.read import get_export_formats_list

templates = Jinja2Templates(directory=Path(__file__).parent / 'templates')


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


def map_license_to_zenodo(license: models.License | None) -> str | None:
    """
    Map MetaCatalog license to Zenodo license identifier.
    Returns None if no mapping exists.
    """
    if license is None:
        return None
    
    license_mapping = {
        'CC BY 4.0': 'cc-by-4.0',
        'CC BY-SA 4.0': 'cc-by-sa-4.0',
        'CC BY-NC 4.0': 'cc-by-nc-4.0',
        'CC BY-NC-SA 4.0': 'cc-by-nc-sa-4.0',
        'ODbL': 'odbl-1.0',
        'ODC-by': 'odc-by-1.0',
        'dl-by-de/2.0': 'dl-de-by-2.0',
    }
    
    return license_mapping.get(license.short_title)


def validate_entry_for_zenodo(entry: models.Metadata) -> tuple[bool, list[str]]:
    """
    Validate that an entry has all required fields for Zenodo upload.
    Returns: (is_valid, missing_fields) where missing_fields is a list of error messages.
    """
    missing_fields = []
    
    # Title is required (but already required by MetaCatalog)
    if not entry.title or not entry.title.strip():
        missing_fields.append("Entry title is required")
    
    # At least one valid creator is required
    valid_creators = []
    
    # Check main author
    if entry.author:
        if entry.author.is_organisation:
            if entry.author.organisation_name and entry.author.organisation_name.strip():
                valid_creators.append(entry.author)
            else:
                missing_fields.append("Author organisation name is required")
        else:
            if (entry.author.first_name and entry.author.first_name.strip() and 
                entry.author.last_name and entry.author.last_name.strip()):
                valid_creators.append(entry.author)
            else:
                missing_fields.append("Author first name and last name are required")
    
    # Check co-authors
    for co_author in entry.coAuthors:
        if co_author.is_organisation:
            if co_author.organisation_name and co_author.organisation_name.strip():
                valid_creators.append(co_author)
        else:
            if (co_author.first_name and co_author.first_name.strip() and 
                co_author.last_name and co_author.last_name.strip()):
                valid_creators.append(co_author)
    
    if len(valid_creators) == 0:
        missing_fields.append("At least one valid creator (with complete name) is required")
    
    # License with valid Zenodo mapping is required
    zenodo_license = map_license_to_zenodo(entry.license)
    if not entry.license:
        missing_fields.append("Entry license is required")
    elif zenodo_license is None:
        missing_fields.append(f"License '{entry.license.short_title}' does not have a Zenodo mapping")
    
    is_valid = len(missing_fields) == 0
    return is_valid, missing_fields


def convert_entry_to_zenodo_metadata(entry: models.Metadata) -> dict:
    """
    Convert MetaCatalog entry to Zenodo metadata format.
    """
    # Build creators list
    creators = []
    
    # Add main author if valid
    if entry.author:
        if entry.author.is_organisation:
            if entry.author.organisation_name and entry.author.organisation_name.strip():
                creator = {
                    "name": entry.author.organisation_name
                }
                if entry.author.organisation_abbrev:
                    creator["name"] = f"{entry.author.organisation_name} ({entry.author.organisation_abbrev})"
                if entry.author.affiliation:
                    creator["affiliation"] = entry.author.affiliation
                if entry.author.orcid:
                    creator["orcid"] = entry.author.orcid
                creators.append(creator)
        else:
            if (entry.author.first_name and entry.author.first_name.strip() and 
                entry.author.last_name and entry.author.last_name.strip()):
                creator = {
                    "name": f"{entry.author.first_name} {entry.author.last_name}"
                }
                if entry.author.affiliation:
                    creator["affiliation"] = entry.author.affiliation
                if entry.author.orcid:
                    creator["orcid"] = entry.author.orcid
                creators.append(creator)
    
    # Add co-authors if valid
    for co_author in entry.coAuthors:
        if co_author.is_organisation:
            if co_author.organisation_name and co_author.organisation_name.strip():
                creator = {
                    "name": co_author.organisation_name
                }
                if co_author.organisation_abbrev:
                    creator["name"] = f"{co_author.organisation_name} ({co_author.organisation_abbrev})"
                if co_author.affiliation:
                    creator["affiliation"] = co_author.affiliation
                if co_author.orcid:
                    creator["orcid"] = co_author.orcid
                creators.append(creator)
        else:
            if (co_author.first_name and co_author.first_name.strip() and 
                co_author.last_name and co_author.last_name.strip()):
                creator = {
                    "name": f"{co_author.first_name} {co_author.last_name}"
                }
                if co_author.affiliation:
                    creator["affiliation"] = co_author.affiliation
                if co_author.orcid:
                    creator["orcid"] = co_author.orcid
                creators.append(creator)
    
    # Build metadata dict
    metadata = {
        "title": entry.title,
        "upload_type": "dataset",
        "description": entry.abstract or entry.title,
        "creators": creators,
    }
    
    # Add license
    zenodo_license = map_license_to_zenodo(entry.license)
    if zenodo_license:
        metadata["license"] = zenodo_license
    
    # Add keywords if available
    if entry.keywords:
        metadata["keywords"] = [kw.value for kw in entry.keywords if kw.value]
    
    # Add publication date
    if entry.publication:
        metadata["publication_date"] = entry.publication.strftime("%Y-%m-%d")
    
    # Add version
    metadata["version"] = str(entry.version)
    
    return {"metadata": metadata}


def create_zenodo_package(request: Request, entry_id: int) -> tuple[io.BytesIO, str]:
    """
    Create a Zenodo-specific package with README.md, metacatalog.json, 
    metadata exports, and data files.
    
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
        # 1. Generate and add README.md
        readme_content = f"# {entry.title}\n\n"
        
        if entry.abstract:
            readme_content += f"## Abstract\n\n{entry.abstract}\n\n"
        
        readme_content += "## About This Record\n\n"
        readme_content += "This record was automatically generated and uploaded by MetaCatalog API.\n\n"
        
        # Generate backlink URL from request
        base_url = f"{request.url.scheme}://{request.url.netloc}"
        entry_url = f"{base_url}/entries/{entry_id}"
        readme_content += f"[View this entry in MetaCatalog]({entry_url})\n"
        
        zip_file.writestr("README.md", readme_content)
        
        # 2. Add metacatalog.json to root
        entry_dict = entry.model_dump(mode='json')
        zip_file.writestr(
            "metacatalog.json",
            json.dumps(entry_dict, indent=2, default=str)
        )
        
        # 3. Add metadata exports to metadata/ folder
        # Add datacite.xml
        try:
            datacite_content = templates.get_template("datacite.xml").render(entry=entry)
            zip_file.writestr("metadata/datacite.xml", datacite_content)
        except TemplateError:
            # Skip if template fails, but continue
            pass
        
        # Add dublincore.xml
        try:
            dublincore_content = templates.get_template("dublincore.xml").render(entry=entry)
            zip_file.writestr("metadata/dublincore.xml", dublincore_content)
        except TemplateError:
            # Skip if template fails, but continue
            pass
        
        # 4. Add data files to data/ folder
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

            csv_content = "".join(data_info['stream_generator']())
            zip_file.writestr(f"data/{data_info['filename']}", csv_content)
        elif data_info['file_path']:
            # File-based datasource - add file to ZIP
            zip_file.write(str(data_info['file_path']), f"data/{data_info['filename']}")
        else:
            # External or unsupported - create manifest
            if entry.datasource:
                if entry.datasource.type.name == "external":
                    manifest = {
                        "type": "external",
                        "url": entry.datasource.path,
                        "description": "External datasource - data not included in package"
                    }
                else:
                    manifest = {
                        "type": entry.datasource.type.name if entry.datasource.type else "unknown",
                        "path": entry.datasource.path,
                        "status": "unsupported",
                        "description": f"Datasource type '{entry.datasource.type.name if entry.datasource.type else 'unknown'}' is not supported for packaging"
                    }
                zip_file.writestr("data/manifest.json", json.dumps(manifest, indent=2))
    
    zip_buffer.seek(0)
    filename = f"entry_{entry_id}_package.zip"
    
    return zip_buffer, filename


@share_router.get('/share/zenodo/form')
def get_zenodo_form(entry_id: int, request: Request):
    """
    Zenodo Upload
    Get form for Zenodo upload
    """
    # Validate entry exists
    entries = core.entries(ids=entry_id)
    if len(entries) == 0:
        raise HTTPException(status_code=404, detail=f"Entry of <ID={entry_id}> not found")
    
    entry = entries[0]
    
    # Validate entry for Zenodo
    is_valid, missing_fields = validate_entry_for_zenodo(entry)
    
    if not is_valid:
        # Return form with error
        return {
            "fields": [
                {
                    "name": "error",
                    "type": "error",
                    "message": f"Entry is missing required fields for Zenodo upload: {', '.join(missing_fields)}"
                }
            ]
        }
    
    # Return form with token and sandbox checkbox
    return {
        "fields": [
            {
                "name": "zenodo_token",
                "type": "text",
                "label": "Zenodo Access Token",
                "required": True,
                "password": True,
                "help_text": "Your Zenodo personal access token. Create one at https://zenodo.org/account/settings/applications/"
            },
            {
                "name": "use_sandbox",
                "type": "checkbox",
                "label": "Use Sandbox (for testing)",
                "default": True,
                "help_text": "Upload to Zenodo sandbox instead of production"
            }
        ],
        "metadata_preview": False
    }


@share_router.post('/share/zenodo/submit')
async def submit_zenodo(entry_id: int, request: Request):
    """
    Submit Zenodo upload request
    """
    # Parse request body
    try:
        body = await request.json()
        zenodo_token = body.get('zenodo_token')
        use_sandbox = body.get('use_sandbox', True)
    except (json.JSONDecodeError, ValueError, TypeError, KeyError) as e:
        raise HTTPException(status_code=400, detail="Invalid request body. Expected JSON with 'zenodo_token' and optional 'use_sandbox' fields.") from e
    
    if not zenodo_token:
        raise HTTPException(status_code=400, detail="zenodo_token is required")
    
    # Strip whitespace from token
    zenodo_token = zenodo_token.strip()
    
    # Validate entry exists
    entries = core.entries(ids=entry_id)
    if len(entries) == 0:
        raise HTTPException(status_code=404, detail=f"Entry of <ID={entry_id}> not found")
    
    entry = entries[0]
    
    # Validate entry for Zenodo
    is_valid, missing_fields = validate_entry_for_zenodo(entry)
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail=f"Entry is missing required fields for Zenodo upload: {', '.join(missing_fields)}"
        )
    
    # Determine Zenodo base URL
    if use_sandbox:
        zenodo_base_url = "https://sandbox.zenodo.org/api"
    else:
        zenodo_base_url = "https://zenodo.org/api"
    
    # Prepare headers for Zenodo API
    headers = {
        "Authorization": f"Bearer {zenodo_token}",
        "Content-Type": "application/json"
    }
    
    # Create Zenodo-specific package
    zip_buffer, zip_filename = create_zenodo_package(request, entry_id)
    zip_data = zip_buffer.read()
    zip_buffer.close()
    
    try:
        # Step 1: Create empty deposition
        async with httpx.AsyncClient() as client:
            create_response = await client.post(
                f"{zenodo_base_url}/deposit/depositions",
                json={},
                headers=headers,
                timeout=30.0
            )
            
            if create_response.status_code not in [200, 201]:
                error_detail = create_response.text
                try:
                    error_json = create_response.json()
                    error_detail = error_json.get('message', error_json.get('status', error_detail))
                    # Log full error response for debugging
                    if error_json:
                        error_detail = f"{error_detail} (Full response: {error_json})"
                except (json.JSONDecodeError, ValueError):
                    # Response is not JSON, use text as-is
                    pass
                
                # Provide helpful error messages for common issues
                if create_response.status_code == 401:
                    error_detail = "Invalid or expired Zenodo access token. Please check your token and try again."
                elif create_response.status_code == 403:
                    error_detail = f"Permission denied. Please ensure: (1) Your token is for the correct environment (sandbox vs production), (2) The token has 'deposit:write' scope, and (3) The token is valid. Error: {error_detail}"
                
                raise HTTPException(
                    status_code=create_response.status_code,
                    detail=f"Failed to create Zenodo deposition: {error_detail}"
                )
            
            deposition = create_response.json()
            bucket_url = deposition["links"]["bucket"]
            deposition_id = deposition["id"]
            
            # Step 2: Upload file to bucket
            upload_headers = {
                "Authorization": f"Bearer {zenodo_token}"
            }
            
            upload_response = await client.put(
                f"{bucket_url}/{zip_filename}",
                content=zip_data,
                headers=upload_headers,
                timeout=60.0
            )
            
            if upload_response.status_code not in [200, 201]:
                error_detail = upload_response.text
                try:
                    error_json = upload_response.json()
                    error_detail = error_json.get('message', error_detail)
                except (json.JSONDecodeError, ValueError):
                    # Response is not JSON, use text as-is
                    pass
                raise HTTPException(
                    status_code=upload_response.status_code,
                    detail=f"Failed to upload file to Zenodo: {error_detail}"
                )
            
            # Step 3: Add metadata
            zenodo_metadata = convert_entry_to_zenodo_metadata(entry)
            
            metadata_response = await client.put(
                f"{zenodo_base_url}/deposit/depositions/{deposition_id}",
                json=zenodo_metadata,
                headers=headers,
                timeout=30.0
            )
            
            if metadata_response.status_code not in [200, 201]:
                error_detail = metadata_response.text
                try:
                    error_json = metadata_response.json()
                    error_detail = error_json.get('message', error_detail)
                except (json.JSONDecodeError, ValueError):
                    # Response is not JSON, use text as-is
                    pass
                raise HTTPException(
                    status_code=metadata_response.status_code,
                    detail=f"Failed to update Zenodo metadata: {error_detail}"
                )
            
            # Get updated deposition
            final_deposition = metadata_response.json()
            
            # Extract pre-reserved DOI (if available)
            prereserved_doi = None
            metadata = final_deposition.get("metadata", {})
            if "prereserve_doi" in metadata:
                prereserved_doi = metadata["prereserve_doi"].get("doi")
            
            # Step 4: Return response with structured fields
            zenodo_links = final_deposition.get("links", {})
            response = {
                "success": True,
                "message": "Entry successfully uploaded to Zenodo.",
                "warning": "The entry is in draft mode. Use the publish link below to make it public and activate the DOI.",
                "links": {
                    "View": zenodo_links.get("html"),
                    "Edit": zenodo_links.get("edit"),
                    "Publish": zenodo_links.get("publish"),
                }
            }
            
            # Add pre-reserved DOI if available
            if prereserved_doi:
                response["prereserved_doi"] = prereserved_doi
                response["message"] = f"Entry successfully uploaded to Zenodo. Pre-reserved DOI: {prereserved_doi} (will be activated upon publishing)."
            
            return response
            
    except HTTPException:
        raise
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Network error while communicating with Zenodo: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during Zenodo upload: {str(e)}"
        )
