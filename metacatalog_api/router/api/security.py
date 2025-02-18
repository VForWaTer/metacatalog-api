from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from metacatalog_api import core
from metacatalog_api import access_control

async def validate_api_key(api_key: str = Security(APIKeyHeader(name="X-API-Key"))):
    with core.connect() as session:
        token = access_control.validate_token(session, api_key) 
        if token is None:
            raise HTTPException(status_code=401, detail="Invalid API key")
        return token
