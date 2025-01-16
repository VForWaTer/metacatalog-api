from fastapi import APIRouter
from fastapi import UploadFile

from metacatalog_api.core import cache


upload_router = APIRouter()

@upload_router.post('/uploads')
def create_new_upload_preview(file: UploadFile, guess_metadata: bool = False):
    file_hash = cache.index_file(file)

    file_info = cache.get_file(file_hash)
    return {
        'file_hash': file_hash,
        'filename': file_info.filename,
        'size': file_info.size
    }

@upload_router.get('/uploads')
def get_all_upload_previews():
    file_infos = list(cache.cache.values())

    return {
        'count': len(file_infos),
        'files': file_infos
    }

