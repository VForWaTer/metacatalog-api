from pathlib import Path
import mimetypes

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from sqlmodel import text

from metacatalog_api import core


data_router = APIRouter()


def yield_error_message(error: str):
    yield f"""# Error
    The requested file could not be streamed back to you.
    I don't know why, but here is a error message for you:
    
    ```
    {error}
    ```
    """

def yield_file(file_path: str):
    with open(file_path, 'rb') as f:
        yield from f


def yield_internal_table(datasource):
    headers = []
    if datasource.temporal_scale is not None:
        headers.extend(datasource.temporal_scale.dimension_names)
    if datasource.spatial_scale is not None:
        headers.extend(datasource.spatial_scale.dimension_names)
    headers.extend(datasource.variable_names)
    yield ",".join(headers) + "\n" 
    sql = text(f"SELECT * FROM {datasource.path};")
    with core.connect() as session:
        for record in session.exec(sql):
            yield ",".join([str(c) for c in record]) + "\n"


@data_router.get('/entries/{entry_id}/dataset')
async def get_dataset(entry_id: int) -> StreamingResponse:
    # get the metadata
    entries = core.entries(ids=entry_id)
    if len(entries) == 0:
        return StreamingResponse(yield_error_message(f"Metadata Entry of id <ID={entry_id}> not found"), media_type="text/markdown")
    
    datasource = entries[0].datasource
    if datasource is None:
        return StreamingResponse(yield_error_message(f"Metadata Entry of id <ID={entry_id}> has no datasource"), media_type="text/markdown")

    # These are two cases that are not yet supported:
    if '*' in datasource.path:
        return StreamingResponse(yield_error_message(f"MetaCatalog API does currently not support streaming of wildcard paths"), media_type="text/markdown")
    elif Path(datasource.path).is_dir(): 
        return StreamingResponse(yield_error_message(f"Metadata Entry of id <ID={entry_id}> points to a directory. GZip result streaming is not yet supported."), media_type="text/markdown")
    
    
    if datasource.type.name == "internal":
        return StreamingResponse(yield_internal_table(datasource), media_type="text/csv")
    elif datasource.type.name == "external":
        return StreamingResponse(yield_error_message(f"Metadata Entry of id <ID={entry_id}> is external and cannot be downloaded"), media_type="text/markdown")
    elif datasource.type.name == "csv":
        return StreamingResponse(yield_file(datasource.path), media_type="text/csv")
    elif datasource.type.name == "local":
        mime, _ = mimetypes.guess_type(datasource.path)
        if mime is None:
            mime = "application/octet-stream"
        return StreamingResponse(yield_file(datasource.path), media_type=mime)
    elif datasource.type.name == "netCDF":
        return StreamingResponse(yield_file(datasource.path), media_type="application/netcdf")
    else:
        return StreamingResponse(yield_error_message(f"Metadata Entry of id <ID={entry_id}> has an unknown datasource type"), media_type="text/markdown")
