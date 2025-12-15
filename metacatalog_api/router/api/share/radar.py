import json
import os
import tempfile
import zipfile
from pathlib import Path

import httpx
from fastapi import Request, HTTPException
from fastapi.templating import Jinja2Templates
from jinja2 import TemplateError

from metacatalog_api import core, models
from metacatalog_api.router.api.share import share_router
from metacatalog_api.server import server


# Templates are in router/api/templates/, we're in router/api/share/
templates = Jinja2Templates(directory=Path(__file__).parent.parent / 'templates')


async def get_radar_token(
    client_id: str,
    client_secret: str,
    username: str,
    password: str,
    redirect_url: str | None,
    base_url: str
) -> dict:
    """
    Get OAuth access token from RADAR using ROPC flow.
    Returns: {"access_token": str, "refresh_token": str, "expires_in": int}
    """
    token_url = f"{base_url}/tokens"
    
    payload = {
        "clientId": client_id,
        "clientSecret": client_secret,
        "userName": username,
        "userPassword": password
    }
    
    if redirect_url:
        payload["redirectUrl"] = redirect_url
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                json=payload,
                timeout=30.0
            )
            
            if response.status_code == 401:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid RADAR credentials. Please check your username and password."
                )
            
            if response.status_code not in [200, 201]:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get('message', error_json.get('status', error_detail))
                except (json.JSONDecodeError, ValueError):
                    pass
                
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to authenticate with RADAR: {error_detail}"
                )
            
            return response.json()
            
    except HTTPException:
        raise
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Network error while communicating with RADAR: {e!s}"
        ) from e


async def refresh_radar_token(
    client_id: str,
    client_secret: str,
    refresh_token: str,
    base_url: str
) -> dict:
    """
    Refresh expired access token.
    Returns: {"access_token": str, "refresh_token": str, "expires_in": int}
    """
    token_url = f"{base_url}/tokens/refresh"
    
    payload = {
        "clientId": client_id,
        "clientSecret": client_secret,
        "refreshToken": refresh_token
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                json=payload,
                timeout=30.0
            )
            
            if response.status_code not in [200, 201]:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get('message', error_detail)
                except (json.JSONDecodeError, ValueError):
                    pass
                
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to refresh RADAR token: {error_detail}"
                )
            
            return response.json()
            
    except HTTPException:
        raise
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Network error while refreshing RADAR token: {e!s}"
        ) from e


def render_zku_xml(entry: models.Metadata, request: Request) -> str:
    """
    Render ZKU XML metadata from entry using existing template.
    Uses the zku.xml template from router/api/templates/
    """
    try:
        zku_content = templates.get_template("zku.xml").render(entry=entry, request=request)
        return zku_content
    except TemplateError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to render ZKU XML template: {e!s}"
        ) from e


async def get_radar_contracts(access_token: str, base_url: str) -> list[dict]:
    """
    Get available contracts for the authenticated user.
    GET /contracts?sort=title&offset=0&rows=100
    """
    contracts_url = f"{base_url}/contracts"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    params = {
        "sort": "title",
        "offset": 0,
        "rows": 100
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                contracts_url,
                headers=headers,
                params=params,
                timeout=30.0
            )
            
            if response.status_code != 200:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get('message', error_detail)
                except (json.JSONDecodeError, ValueError):
                    pass
                
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to fetch RADAR contracts: {error_detail}"
                )
            
            result = response.json()
            # RADAR API may return contracts in different formats
            if isinstance(result, list):
                return result
            elif isinstance(result, dict) and 'results' in result:
                return result['results']
            elif isinstance(result, dict) and 'contracts' in result:
                return result['contracts']
            else:
                return []
            
    except HTTPException:
        raise
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Network error while fetching RADAR contracts: {e!s}"
        ) from e


async def get_radar_workspaces(access_token: str, contract_id: str, base_url: str) -> list[dict]:
    """
    Get available workspaces for a contract.
    GET /contracts/{contractId}/workspaces
    """
    workspaces_url = f"{base_url}/contracts/{contract_id}/workspaces"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                workspaces_url,
                headers=headers,
                timeout=30.0
            )
            
            if response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail=f"Contract with ID '{contract_id}' not found or you don't have access to it"
                )
            
            if response.status_code != 200:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get('message', error_detail)
                except (json.JSONDecodeError, ValueError):
                    pass
                
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to fetch RADAR workspaces: {error_detail}"
                )
            
            result = response.json()
            # RADAR API may return workspaces in different formats
            if isinstance(result, list):
                return result
            elif isinstance(result, dict) and 'results' in result:
                return result['results']
            elif isinstance(result, dict) and 'workspaces' in result:
                return result['workspaces']
            else:
                return []
            
    except HTTPException:
        raise
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Network error while fetching RADAR workspaces: {e!s}"
        ) from e


async def create_radar_dataset(access_token: str, workspace_id: str, base_url: str) -> dict:
    """
    Create a new dataset in RADAR workspace.
    POST /workspaces/{workspaceId}/datasets
    
    Creates with minimal metadata (empty descriptiveMetadata).
    Returns dataset object with id, uploadURL, ingestURL, links.
    """
    datasets_url = f"{base_url}/workspaces/{workspace_id}/datasets"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Create with minimal metadata
    payload = {
        "descriptiveMetadata": {}
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                datasets_url,
                json=payload,
                headers=headers,
                timeout=30.0
            )
            
            if response.status_code == 403:
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission denied. You may not have access to workspace '{workspace_id}' or the contract."
                )
            
            if response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail=f"Workspace with ID '{workspace_id}' not found"
                )
            
            if response.status_code not in [200, 201]:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get('message', error_detail)
                except (json.JSONDecodeError, ValueError):
                    pass
                
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to create RADAR dataset: {error_detail}"
                )
            
            return response.json()
            
    except HTTPException:
        raise
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Network error while creating RADAR dataset: {e!s}"
        ) from e


async def import_radar_metadata(access_token: str, dataset_id: str, zku_xml: str, base_url: str) -> None:
    """
    Import ZKU XML metadata into RADAR dataset.
    POST /datasets/{id}/metadata
    
    This is step 2 in upload flow (metadata first).
    """
    metadata_url = f"{base_url}/datasets/{dataset_id}/metadata"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/xml"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                metadata_url,
                content=zku_xml.encode('utf-8'),
                headers=headers,
                timeout=60.0
            )
            
            if response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail=f"Dataset with ID '{dataset_id}' not found"
                )
            
            if response.status_code == 422:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get('message', error_detail)
                except (json.JSONDecodeError, ValueError):
                    pass
                
                raise HTTPException(
                    status_code=422,
                    detail=f"RADAR metadata validation failed: {error_detail}. Please check the ZKU XML format."
                )
            
            if response.status_code not in [200, 201]:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get('message', error_detail)
                except (json.JSONDecodeError, ValueError):
                    pass
                
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to import RADAR metadata: {error_detail}"
                )
            
    except HTTPException:
        raise
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Network error while importing RADAR metadata: {e!s}"
        ) from e


async def upload_to_radar(access_token: str, upload_url: str, file_path: str, filename: str) -> None:
    """
    Upload file to RADAR using the uploadURL from dataset creation.
    PUT {uploadURL}/{filename}
    
    This is step 3 in upload flow (data after metadata).
    File is cleaned up by caller after upload.
    """
    upload_full_url = f"{upload_url}/{filename}"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            # Stream file from disk
            with open(file_path, 'rb') as f:
                response = await client.put(
                    upload_full_url,
                    content=f.read(),
                    headers=headers,
                    timeout=300.0  # Longer timeout for large files
                )
            
            if response.status_code not in [200, 201]:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get('message', error_detail)
                except (json.JSONDecodeError, ValueError):
                    pass
                
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to upload file to RADAR: {error_detail}"
                )
            
    except HTTPException:
        raise
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Network error while uploading file to RADAR: {e!s}"
        ) from e
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail=f"Temporary file not found: {file_path}"
        )


def create_radar_package(request: Request, entry_id: int) -> tuple[str, str]:
    """
    Create a RADAR-specific package with:
    - ZKU XML metadata (from zku.xml template)
    - Data files (if available)
    
    Similar to create_zenodo_package but uses temporary file instead of memory.
    Returns (temp_file_path, filename) where temp_file_path is the path to the temporary ZIP file.
    Caller is responsible for cleanup (delete temp file after upload).
    """
    # Get entry metadata
    entries = core.entries(ids=entry_id)
    if len(entries) == 0:
        raise HTTPException(status_code=404, detail=f"Entry of <ID={entry_id}> not found")
    
    entry = entries[0]
    
    # Create temporary ZIP file on disk
    temp_fd, temp_path = tempfile.mkstemp(suffix='.zip', prefix='radar_upload_')
    os.close(temp_fd)  # Close file descriptor, we'll use the path
    
    try:
        with zipfile.ZipFile(temp_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # 1. Add ZKU XML metadata
            try:
                zku_xml = render_zku_xml(entry, request)
                zip_file.writestr("metadata/zku.xml", zku_xml)
            except Exception as e:
                # If ZKU XML fails, continue but log
                # We'll still upload metadata separately via API
                pass
            
            # 2. Add data files to data/ folder
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
        
        filename = f"entry_{entry_id}_package.zip"
        return temp_path, filename
        
    except Exception as e:
        # Clean up temp file on error
        try:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        except Exception:
            pass
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create RADAR package: {e!s}"
        ) from e


@share_router.get('/share/radar/form')
def get_radar_form(entry_id: int, request: Request):
    """
    RADAR Upload
    Get form for RADAR upload
    """
    # Validate entry exists
    entries = core.entries(ids=entry_id)
    if len(entries) == 0:
        raise HTTPException(status_code=404, detail=f"Entry of <ID={entry_id}> not found")
    
    # Return form with fields
    # Note: If RADAR is not configured, we still return the form but it will fail on submit
    # This allows the UI to show the form and provide a better error message
    return {
        "fields": [
            {
                "name": "radar_username",
                "type": "text",
                "label": "RADAR Username",
                "required": True,
                "help": "Your RADAR username (must be registered via local RADAR database, not Shibboleth)"
            },
            {
                "name": "radar_password",
                "type": "password",
                "label": "RADAR Password",
                "required": True,
                "help": "Your RADAR password"
            },
            {
                "name": "contract_id",
                "type": "text",
                "label": "Contract ID",
                "required": True,
                "help": "The RADAR contract ID where the dataset will be created"
            },
            {
                "name": "workspace_id",
                "type": "text",
                "label": "Workspace ID",
                "required": True,
                "help": "The RADAR workspace ID where the dataset will be created"
            },
            {
                "name": "use_production",
                "type": "checkbox",
                "label": "Use Production Environment",
                "default": False,
                "help": "Upload to RADAR production instead of test environment"
            }
        ],
        "metadata_preview": False
    }


@share_router.post('/share/radar/submit')
async def submit_radar(entry_id: int, request: Request):
    """
    Submit RADAR upload request
    """
    # Parse request body
    try:
        body = await request.json()
        radar_username = body.get('radar_username')
        radar_password = body.get('radar_password')
        contract_id = body.get('contract_id')
        workspace_id = body.get('workspace_id')
        use_production = body.get('use_production', False)
    except (json.JSONDecodeError, ValueError, TypeError, KeyError) as e:
        raise HTTPException(
            status_code=400,
            detail="Invalid request body. Expected JSON with 'radar_username', 'radar_password', 'contract_id', 'workspace_id', and optional 'use_production' fields."
        ) from e
    
    # Validate required fields
    if not radar_username or not radar_password:
        raise HTTPException(status_code=400, detail="radar_username and radar_password are required")
    if not contract_id or not workspace_id:
        raise HTTPException(status_code=400, detail="contract_id and workspace_id are required")
    
    # Get RADAR client credentials from server settings
    if not server.radar_client_id or not server.radar_client_secret:
        raise HTTPException(
            status_code=500,
            detail="RADAR is not configured. Please contact the administrator."
        )
    
    # Determine base URL (test vs production)
    if use_production:
        base_url = "https://www.radar-service.eu/radar/api"
    else:
        base_url = server.radar_base_url
    
    temp_file_path = None
    
    try:
        # Step 1: Authenticate with RADAR → get access token
        token_response = await get_radar_token(
            client_id=server.radar_client_id,
            client_secret=server.radar_client_secret,
            username=radar_username,
            password=radar_password,
            redirect_url=server.radar_redirect_url,
            base_url=base_url
        )
        
        access_token = token_response.get('access_token')
        if not access_token:
            raise HTTPException(
                status_code=500,
                detail="RADAR authentication failed: no access token received"
            )
        
        # Clear password from memory (best effort)
        radar_password = None
        del radar_password
        
        # Step 2: Validate entry exists
        entries = core.entries(ids=entry_id)
        if len(entries) == 0:
            raise HTTPException(status_code=404, detail=f"Entry of <ID={entry_id}> not found")
        
        entry = entries[0]
        
        # Step 3: Create dataset in workspace (minimal metadata)
        dataset = await create_radar_dataset(
            access_token=access_token,
            workspace_id=workspace_id,
            base_url=base_url
        )
        
        dataset_id = dataset.get('id')
        upload_url = dataset.get('uploadURL')
        
        if not dataset_id:
            raise HTTPException(
                status_code=500,
                detail="Failed to create RADAR dataset: no dataset ID returned"
            )
        
        if not upload_url:
            raise HTTPException(
                status_code=500,
                detail="Failed to create RADAR dataset: no uploadURL returned"
            )
        
        # Step 4: Render ZKU XML from entry
        zku_xml = render_zku_xml(entry, request)
        
        # Step 5: Import ZKU XML metadata (POST /datasets/{id}/metadata)
        await import_radar_metadata(
            access_token=access_token,
            dataset_id=dataset_id,
            zku_xml=zku_xml,
            base_url=base_url
        )
        
        # Step 6: Create ZIP package in temporary file (on disk, not memory)
        temp_file_path, zip_filename = create_radar_package(request, entry_id)
        
        # Step 7: Upload ZIP file to dataset (PUT {uploadURL}/package.zip) - stream from disk
        await upload_to_radar(
            access_token=access_token,
            upload_url=upload_url,
            file_path=temp_file_path,
            filename=zip_filename
        )
        
        # Step 8: Clean up temporary ZIP file (delete after successful upload)
        try:
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                temp_file_path = None
        except Exception as cleanup_error:
            # Log but don't fail the request
            pass
        
        # Step 9: Return success response with dataset URL and links
        dataset_links = dataset.get('links', {})
        response = {
            "success": True,
            "message": "Entry successfully uploaded to RADAR.",
            "dataset_id": dataset_id,
            "links": {
                "View": dataset_links.get('html'),
                "Edit": dataset_links.get('edit'),
            }
        }
        
        return response
        
    except HTTPException:
        # Clean up temp file on error
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception:
                pass
        raise
    except Exception as e:
        # Clean up temp file on error
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception:
                pass
        
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during RADAR upload: {e!s}"
        ) from e

