from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

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


def yield_file(file_path: Path):
    with open(file_path, 'rb') as f:
        yield from f


@data_router.get('/entries/{entry_id}/data')
@data_router.get('/entries/{entry_id}/dataset')  # Keep old endpoint for backwards compatibility
async def get_dataset(entry_id: int) -> StreamingResponse:
    """
    Get data file for an entry.
    Uses core.get_entry_data_file() to handle all datasource types.
    """
    # Get data file info from core function
    data_info = core.get_entry_data_file(entry_id)
    
    # Handle errors
    if data_info['error']:
        return StreamingResponse(
            yield_error_message(data_info['error']),
            media_type="text/markdown"
        )
    
    # Prepare headers
    headers = {
        'Content-Disposition': f'attachment; filename="{data_info["filename"]}"'
    }
    
    # Handle streaming data (internal tables)
    if data_info['is_stream']:
        return StreamingResponse(
            data_info['stream_generator'](),
            media_type=data_info['mime_type'],
            headers=headers
        )
    
    # Handle file-based data
    if data_info['file_path']:
        return StreamingResponse(
            yield_file(data_info['file_path']),
            media_type=data_info['mime_type'],
            headers=headers
        )
    
    # Fallback error
    return StreamingResponse(
        yield_error_message("Unknown error occurred while retrieving data"),
        media_type="text/markdown"
    )
