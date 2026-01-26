from fastapi import Request, Depends
from fastapi.responses import FileResponse, JSONResponse
from starlette.middleware.cors import CORSMiddleware

from metacatalog_api.server import app, server

# these imports load the functionality needed for this metacatalog server
from metacatalog_api.apps.manager.router import router as manager_router
from metacatalog_api.router.api.read import read_router as api_read_router
from metacatalog_api.router.api.create import create_router as api_create_router
from metacatalog_api.router.api.upload import upload_router
from metacatalog_api.router.api.data import data_router
from metacatalog_api.router.api.preview import preview_router
from metacatalog_api.router.api.export import export_router as api_export_router
from metacatalog_api.router.api.share import share_router as api_share_router
from metacatalog_api.router.api.security import validate_api_key, router as security_router

# Import share providers to register their routes
from metacatalog_api.router.api.share import download, zenodo, radar  # noqa: F401

# at first we add the cors middleware to allow everyone to reach the API
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# the main page is defined here
# this can easily be changed to a different entrypoint
@app.get('/')
def index(request: Request):
    """
    Main page - redirect to the manager application
    """
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/manager", status_code=302)


# add all api routes - currently this is only splitted into read and create
app.include_router(api_read_router)
app.include_router(api_export_router)
app.include_router(api_share_router)
app.include_router(api_create_router, dependencies=[Depends(validate_api_key)])
app.include_router(upload_router, dependencies=[Depends(validate_api_key)])
app.include_router(data_router, dependencies=[Depends(validate_api_key)])
app.include_router(preview_router, prefix="/preview", dependencies=[Depends(validate_api_key)])
app.include_router(security_router)

# add the manager application (SvelteKit)
app.include_router(manager_router)

# Serve manager SPA - check if file exists, otherwise serve index.html
import os
dist_dir = "metacatalog_api/apps/manager/dist"

@app.get("/manager")
async def serve_manager():
    index_path = os.path.join(dist_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse(status_code=404, content={"detail": "Not Found"})

@app.get("/manager/{file_path:path}")
async def serve_manager_file(file_path: str):
    full_path = os.path.join(dist_dir, file_path)
    if os.path.isfile(full_path):
        return FileResponse(full_path)
    # File doesn't exist, serve index.html for SPA routing
    index_path = os.path.join(dist_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse(status_code=404, content={"detail": "Not Found"})


if __name__ == '__main__':
    # run the server
    server.cli_cmd('default_server:app')
