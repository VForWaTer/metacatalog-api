from fastapi import Request
from starlette.middleware.cors import CORSMiddleware

from metacatalog_api.server import app, server

# these imports load the functionality needed for this metacatalog server
from metacatalog_api.apps.explorer.read import templates
from metacatalog_api.router.api.read import read_router as api_read_router
from metacatalog_api.router.api.create import create_router as api_create_router
from metacatalog_api.apps.explorer.create import create_router as explorer_create
from metacatalog_api.apps.explorer.read import explorer_router

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
    Main page for the HTML Metacatalog Explorer.
    This example app includes the explorer read and create routes
    which are powered by the api route
    """
    return templates.TemplateResponse(request=request, name="index.html", context={"path": server.uri_prefix})


# add all api routes - currently this is only splitted into read and create
app.include_router(api_read_router)
app.include_router(api_create_router)

# add the default explorer application (the HTML)
app.include_router(explorer_router, prefix=f"/{server.app_name}")
app.include_router(explorer_create, prefix=f"/{server.app_name}")


if __name__ == '__main__':
    # run the server
    server.cli_cmd('default_server:app')
