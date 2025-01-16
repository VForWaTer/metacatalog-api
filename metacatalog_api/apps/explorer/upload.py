from pathlib import Path

from fastapi import APIRouter, Request, UploadFile
from fastapi.templating import Jinja2Templates

from metacatalog_api import core
from metacatalog_api.server import server

upload_router = APIRouter()


templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

@upload_router.get("/upload/upload_file.html")
def get_upload_template(request: Request):
    return templates.TemplateResponse(request=request, name="upload_file.html", context={"path": server.app_prefix, "root_path": server.uri_prefix})

@upload_router.post("/uploads")
def get_upload_file(request: Request, file: UploadFile):
    file_hash = core.cache.index_file(file)
    file_info = core.cache.get_file(file_hash)
    file_extension = file_info.filename.split('.')[-1].lower()
    
    available_types = core.datatypes()
    names = list(map(lambda x: x.name.lower(), available_types))
    if file_extension in names:
        types = list(filter(lambda x: x.name.lower() == file_extension, available_types))
    else:
        whitelist = ['local', 'csv', 'netcdf']
        types = list(filter(lambda x: x.name.lower() in whitelist, available_types))
    

    return templates.TemplateResponse(
        request=request,
        name="add_datasource.html", 
        context={
            "path": server.app_prefix, 
            "root_path": server.uri_prefix, 
            "file_hash": file_hash, 
            "file_info": file_info,
            "types": types
        }
    )
