import json
import logging
import os
import secrets
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urlencode

import httpx
from fastapi import Request, HTTPException, Query
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from jinja2 import TemplateError

from metacatalog_api import core, models
from metacatalog_api.router.api.share import share_router
from metacatalog_api.server import server

logger = logging.getLogger(__name__)


# Templates are in router/api/templates/, we're in router/api/share/
templates = Jinja2Templates(directory=Path(__file__).parent.parent / 'templates')


async def exchange_code_for_token(
    code: str,
    state: str,
    client_id: str,
    client_secret: str,
    redirect_url: str | None,
    base_url: str
) -> dict:
    """
    Exchange OAuth authorization code for access token using Authorization Code flow.
    Returns: {"access_token": str, "refresh_token": str, "expires_in": int}
    """
    token_url = f"{base_url}/oauth/token"
    logger.info(f"Exchanging code for token at {token_url}")
    
    # RADAR OAuth token endpoint requires Basic Auth and form-encoded body
    # Basic Auth: client_id:client_secret
    # Body: code, state, redirect_uri, grant_type=authorization_code
    auth = (client_id, client_secret)
    data = {
        "code": code,
        "state": state,
        "grant_type": "authorization_code"
    }
    
    if redirect_url:
        data["redirect_uri"] = redirect_url
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                auth=auth,
                data=data,  # form-encoded, not JSON
                timeout=30.0
            )
            
            logger.info(f"RADAR token exchange response: status={response.status_code}")
            
            if response.status_code == 401:
                logger.error(f"RADAR token exchange 401: {response.text}")
                raise HTTPException(
                    status_code=401,
                    detail="Invalid authorization code or state. Please try authenticating again."
                )
            
            if response.status_code not in [200, 201]:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get('message', error_json.get('status', error_detail))
                except (json.JSONDecodeError, ValueError):
                    pass
                
                logger.error(f"RADAR token exchange failed: {response.status_code} - {error_detail}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to exchange authorization code for token: {error_detail}"
                )
            
            return response.json()
            
    except HTTPException:
        raise
    except httpx.HTTPError as e:
        logger.error(f"RADAR token exchange network error: {e!s}")
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
    RADAR API: POST /tokens/refresh with JSON body.
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


async def get_token_via_password(
    user_name: str,
    user_password: str,
    client_id: str,
    client_secret: str,
    redirect_url: str,
    base_url: str
) -> dict:
    """
    Get RADAR access token via username/password (RADAR API: POST /tokens).
    Body: clientId, clientSecret, redirectUrl, userName, userPassword.
    Returns: {"access_token": str, "refresh_token": str?, "expires_in": int?}
    """
    token_url = f"{base_url}/tokens"
    payload = {
        "clientId": client_id,
        "clientSecret": client_secret,
        "redirectUrl": redirect_url,
        "userName": user_name,
        "userPassword": user_password
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
                    error_detail = error_json.get('message', error_json.get('status', error_detail))
                except (json.JSONDecodeError, ValueError):
                    pass
                logger.error(f"RADAR password token failed: {response.status_code} - {error_detail}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"RADAR login failed: {error_detail}"
                )
            return response.json()
    except HTTPException:
        raise
    except httpx.HTTPError as e:
        logger.error(f"RADAR password token network error: {e!s}")
        raise HTTPException(
            status_code=500,
            detail=f"Network error while communicating with RADAR: {e!s}"
        ) from e


def generate_oauth_state() -> str:
    """
    Generate a secure random state parameter for OAuth flow.
    Used to prevent CSRF attacks.
    """
    return secrets.token_urlsafe(32)


@share_router.get('/share/radar/authorize')
def authorize_radar(request: Request, entry_id: int | None = None):
    """
    Initiate OAuth Authorization Code flow.
    Returns redirect URL to RADAR's OAuth authorize endpoint.
    """
    logger.info("RADAR authorize endpoint called")
    try:
        logger.info(f"RADAR authorize request: entry_id={entry_id}")
        
        if not server.radar_client_id or not server.radar_redirect_url:
            logger.error("RADAR OAuth not configured: client_id={}, redirect_url={}".format(
                bool(server.radar_client_id), bool(server.radar_redirect_url)
            ))
            raise HTTPException(
                status_code=500,
                detail="RADAR OAuth is not configured. Please contact the administrator."
            )
        
        # Generate secure state parameter
        state = generate_oauth_state()
        logger.info(f"Generated OAuth state: {state[:16]}...")
        
        # Store state in app state (in-memory, process-local)
        # In production, use proper session storage (Redis, database, etc.)
        if not hasattr(request.app.state, 'oauth_states'):
            request.app.state.oauth_states = {}
        request.app.state.oauth_states[state] = {
            'timestamp': json.dumps({'created_at': None}),
            'entry_id': entry_id  # Store entry_id to redirect back after OAuth
        }
        logger.info(f"RADAR state stored: {state[:16]}... (total states: {len(request.app.state.oauth_states)})")
        
        # Build OAuth authorize URL
        params = {
            'client_id': server.radar_client_id,
            'response_type': 'code',
            'redirect_uri': server.radar_redirect_url,
            'state': state
        }
        
        # Use test environment by default (can be overridden by provider config)
        base_url = server.radar_base_url
        authorize_url = f"{base_url}/oauth/authorize?{urlencode(params)}"
        logger.info(f"RADAR authorize URL: {base_url}/oauth/authorize (redirect_uri={server.radar_redirect_url})")
        
        # Redirect directly to RADAR OAuth endpoint
        return RedirectResponse(url=authorize_url, status_code=302)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RADAR authorize error: {type(e).__name__}: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {type(e).__name__}: {e!s}"
        ) from e


@share_router.get('/share/radar/callback')
async def callback_radar(
    request: Request, 
    code: str = Query(..., alias="code"),
    state: str | None = Query(None, alias="state")
):
    """
    Handle OAuth callback from RADAR.
    Exchange authorization code for access token.
    """
    logger.error(f"RADAR callback received: code={'present' if code else 'missing'}, state={'present' if state else 'missing'}")
    logger.error(f"Request URL: {request.url}")
    logger.error(f"Query params: {dict(request.query_params)}")
    
    # Check if session is available
    if not hasattr(request, 'session'):
        logger.error("SessionMiddleware not available - request.session attribute missing")
        raise HTTPException(
            status_code=500,
            detail="Session support not available. SessionMiddleware must be installed."
        )
    
    if not code:
        logger.error("RADAR callback missing authorization code")
        raise HTTPException(
            status_code=400,
            detail="Authorization code not received from RADAR"
        )
    
    if not state:
        logger.error("RADAR callback missing state parameter")
        raise HTTPException(
            status_code=400,
            detail="State parameter not received from RADAR"
        )
    
    # Verify state parameter exists (basic CSRF protection)
    if not hasattr(request.app.state, 'oauth_states'):
        logger.error("RADAR callback: oauth_states not initialized in app.state")
        request.app.state.oauth_states = {}
    
    logger.info(f"RADAR callback checking state: {state[:16] if state else 'None'}... (available states: {list(request.app.state.oauth_states.keys())[:3] if request.app.state.oauth_states else 'none'}...)")
    
    if state not in request.app.state.oauth_states:
        logger.error(f"RADAR callback invalid state: {state[:16] if state else 'None'}... (available states: {list(request.app.state.oauth_states.keys())[:3] if request.app.state.oauth_states else 'none'}...)")
        raise HTTPException(
            status_code=400,
            detail="Invalid state parameter. Possible CSRF attack detected."
        )
    
    # Get entry_id from state before cleaning up
    state_data = request.app.state.oauth_states.get(state, {})
    entry_id = state_data.get('entry_id')
    logger.info(f"RADAR callback state valid, entry_id={entry_id}")
    
    # Clean up state (one-time use)
    del request.app.state.oauth_states[state]
    
    # Get RADAR configuration
    if not server.radar_client_id or not server.radar_client_secret:
        logger.error("RADAR OAuth not configured in callback")
        raise HTTPException(
            status_code=500,
            detail="RADAR OAuth is not configured. Please contact the administrator."
        )
    
    # Token exchange endpoint is at /radar-backend/oauth/token
    # OAuth authorize is at /radar-backend/oauth/authorize
    # Token exchange is at /radar-backend/oauth/token (not /radar/api/tokens)
    token_base_url = server.radar_base_url
    logger.info(f"RADAR callback exchanging code for token at {token_base_url}/oauth/token")
    
    try:
        # Exchange code for access token
        token_response = await exchange_code_for_token(
            code=code,
            state=state,
            client_id=server.radar_client_id,
            client_secret=server.radar_client_secret,
            redirect_url=server.radar_redirect_url,
            base_url=token_base_url
        )
        
        logger.info("RADAR token exchange successful")
        
        access_token = token_response.get('access_token')
        if not access_token:
            logger.error("RADAR token response missing access_token")
            raise HTTPException(
                status_code=500,
                detail="Failed to obtain access token from RADAR"
            )
        
        # Store token in session (server-side, not visible to browser)
        try:
            request.session['radar_access_token'] = access_token
            if token_response.get('refresh_token'):
                request.session['radar_refresh_token'] = token_response.get('refresh_token')
            if token_response.get('expires_in'):
                request.session['radar_token_expires_in'] = token_response.get('expires_in')
            logger.info("RADAR token stored in session successfully")
        except AttributeError as e:
            logger.error(f"Failed to access session: {e!s}")
            raise HTTPException(
                status_code=500,
                detail="Session support not available. SessionMiddleware must be installed and configured."
            ) from e
        except Exception as e:
            logger.error(f"Failed to store token in session: {type(e).__name__}: {e!s}")
            raise
        
        logger.info(f"RADAR token stored in session, redirecting to entry_id={entry_id}")
        
        # Redirect to frontend - token is now in session, accessible via session cookie
        from fastapi.responses import RedirectResponse
        if entry_id:
            return RedirectResponse(url=f"/manager/datasets/{entry_id}", status_code=302)
        else:
            return RedirectResponse(url="/manager/list", status_code=302)
        
    except HTTPException as e:
        logger.error(f"RADAR callback HTTPException: {e.status_code} - {e.detail}")
        raise
    except Exception as e:
        logger.error(f"RADAR callback unexpected error: {type(e).__name__}: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during OAuth callback: {e!s}"
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


@share_router.post('/share/radar/login')
async def radar_login(request: Request):
    """
    Log in to RADAR via username/password (RADAR API POST /tokens).
    Stores access token in session for use by submit.
    """
    if not hasattr(request, 'session'):
        raise HTTPException(
            status_code=500,
            detail="Session support not available. SessionMiddleware must be installed."
        )
    if not server.radar_client_id or not server.radar_client_secret or not server.radar_redirect_url:
        raise HTTPException(
            status_code=500,
            detail="RADAR is not configured (client_id, client_secret, redirect_url required)."
        )
    try:
        body = await request.json()
        user_name = (body.get('userName') or body.get('radar_username') or '').strip()
        user_password = body.get('userPassword') or body.get('radar_password') or ''
        use_production = body.get('use_production', False)
    except (json.JSONDecodeError, ValueError, TypeError):
        raise HTTPException(status_code=400, detail="JSON body with userName and userPassword required.")
    if not user_name or not user_password:
        raise HTTPException(status_code=400, detail="userName and userPassword are required.")
    base_url = "https://www.radar-service.eu/radar/api" if use_production else server.radar_base_url
    token_response = await get_token_via_password(
        user_name=user_name,
        user_password=user_password,
        client_id=server.radar_client_id,
        client_secret=server.radar_client_secret,
        redirect_url=server.radar_redirect_url,
        base_url=base_url
    )
    access_token = token_response.get('access_token')
    if not access_token:
        raise HTTPException(status_code=500, detail="RADAR did not return an access token.")
    request.session['radar_access_token'] = access_token
    if token_response.get('refresh_token'):
        request.session['radar_refresh_token'] = token_response.get('refresh_token')
    if token_response.get('expires_in'):
        request.session['radar_token_expires_in'] = token_response.get('expires_in')
    return {"success": True, "message": "Logged in to RADAR."}


@share_router.get('/share/radar/form')
def get_radar_form(entry_id: int, request: Request):
    """
    RADAR upload
    Form uses password-based token (RADAR API POST /tokens).
    Contract/workspace fields omitted when set in env.
    """
    entries = core.entries(ids=entry_id)
    if len(entries) == 0:
        raise HTTPException(status_code=404, detail=f"Entry of <ID={entry_id}> not found")

    fields = [
        {
            "name": "radar_username",
            "type": "text",
            "label": "RADAR username",
            "required": True,
            "help": "RADAR account (local ID/password account, not Shibboleth)"
        },
        {
            "name": "radar_password",
            "type": "password",
            "label": "RADAR password",
            "required": True,
            "help": "RADAR password"
        },
        {
            "name": "use_production",
            "type": "checkbox",
            "label": "Use Production Environment",
            "default": False,
            "help": "Upload to RADAR production instead of test environment"
        }
    ]
    if not server.radar_contract_id or not server.radar_workspace_id:
        fields.extend([
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
            }
        ])

    return {
        "auth_type": "password",
        "provider_token_key": "radar_token",
        "login_endpoint": "/share/radar/login",
        "fields": fields,
        "metadata_preview": False
    }


@share_router.post('/share/radar/submit')
async def submit_radar(entry_id: int, request: Request):
    """
    Submit RADAR upload. Uses session token, or logs in with radar_username/radar_password from body if no token.
    """
    access_token = request.session.get('radar_access_token')
    try:
        body = await request.json()
        use_production = body.get('use_production', False)
        contract_id = body.get('contract_id') or server.radar_contract_id
        workspace_id = body.get('workspace_id') or server.radar_workspace_id
        radar_username = (body.get('radar_username') or '').strip()
        radar_password = body.get('radar_password') or ''
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        raise HTTPException(
            status_code=400,
            detail="Invalid request body. Expected JSON with radar_username, radar_password, and optionally contract_id, workspace_id, use_production."
        ) from e

    if not access_token and (radar_username and radar_password):
        if not server.radar_client_id or not server.radar_client_secret or not server.radar_redirect_url:
            raise HTTPException(status_code=500, detail="RADAR is not configured.")
        base_url = "https://www.radar-service.eu/radar/api" if use_production else server.radar_base_url
        token_response = await get_token_via_password(
            user_name=radar_username,
            user_password=radar_password,
            client_id=server.radar_client_id,
            client_secret=server.radar_client_secret,
            redirect_url=server.radar_redirect_url,
            base_url=base_url
        )
        access_token = token_response.get('access_token')
        if access_token:
            request.session['radar_access_token'] = access_token
            if token_response.get('refresh_token'):
                request.session['radar_refresh_token'] = token_response.get('refresh_token')
            if token_response.get('expires_in'):
                request.session['radar_token_expires_in'] = token_response.get('expires_in')

    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated with RADAR. Enter RADAR username and password, or log in first."
        )
    if not contract_id or not workspace_id:
        raise HTTPException(status_code=400, detail="contract_id and workspace_id are required (or set in env).")

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
        # Step 1: Validate entry exists
        entries = core.entries(ids=entry_id)
        if len(entries) == 0:
            raise HTTPException(status_code=404, detail=f"Entry of <ID={entry_id}> not found")

        entry = entries[0]

        # Step 2: Create dataset in workspace (minimal metadata)
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

        # Step 3: Render ZKU XML from entry
        zku_xml = render_zku_xml(entry, request)

        # Step 4: Import ZKU XML metadata (POST /datasets/{id}/metadata)
        await import_radar_metadata(
            access_token=access_token,
            dataset_id=dataset_id,
            zku_xml=zku_xml,
            base_url=base_url
        )

        # Step 5: Create ZIP package in temporary file (on disk, not memory)
        temp_file_path, zip_filename = create_radar_package(request, entry_id)

        # Step 6: Upload ZIP file to dataset (PUT {uploadURL}/package.zip) - stream from disk
        await upload_to_radar(
            access_token=access_token,
            upload_url=upload_url,
            file_path=temp_file_path,
            filename=zip_filename
        )

        # Step 7: Clean up temporary ZIP file (delete after successful upload)
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

