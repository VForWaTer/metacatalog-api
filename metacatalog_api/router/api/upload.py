from fastapi import APIRouter
from fastapi import UploadFile
import mimetypes
from pathlib import Path

from metacatalog_api.core import cache


upload_router = APIRouter()

@upload_router.post('/uploads')
def create_new_upload_preview(file: UploadFile, guess_metadata: bool = False):
    file_hash = cache.index_file(file)

    file_info = cache.get_file(file_hash)
    
    # Detect mimetype
    detected_mime, _ = mimetypes.guess_type(file_info.filename)
    if detected_mime is None:
        # Fallback based on file extension
        file_extension = Path(file_info.filename).suffix.lower()
        if file_extension == '.csv':
            detected_mime = 'text/csv'
        elif file_extension in ['.nc', '.netcdf', '.cdf']:
            detected_mime = 'application/netcdf'
        else:
            detected_mime = 'application/octet-stream'
    
    return {
        'file_hash': file_hash,
        'filename': file_info.filename,
        'size': file_info.size,
        'mimetype': detected_mime,
        'extension': Path(file_info.filename).suffix.lower()
    }

@upload_router.get('/uploads')
def get_all_upload_previews():
    file_infos = list(cache.cache.values())

    return {
        'count': len(file_infos),
        'files': file_infos
    }

