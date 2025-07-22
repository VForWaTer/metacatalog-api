from fastapi import HTTPException, Security, APIRouter
from fastapi.security import APIKeyHeader

from metacatalog_api import core
from metacatalog_api import access_control

router = APIRouter()

async def validate_api_key(api_key: str = Security(APIKeyHeader(name="X-API-Key"))):
    with core.connect() as session:
        token = access_control.validate_token(session, api_key) 
        if token is None:
            raise HTTPException(status_code=401, detail="Invalid API key")
        return token

@router.get("/validate")
async def validate_token(api_key: str = Security(APIKeyHeader(name="X-API-Key"))):
    """
    Validate an API key and return token information
    """
    with core.connect() as session:
        token = access_control.validate_token(session, api_key)
        if token is None:
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        return {
            "valid": True,
            "token_id": token.id,
            "message": "Token is valid"
        }
