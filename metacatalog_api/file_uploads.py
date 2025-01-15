from typing import Dict, Any
import hashlib
import json
from pathlib import Path
import shutil
from datetime import datetime

from pydantic_settings import BaseSettings
from pydantic import BaseModel, field_serializer
from fastapi import UploadFile


class FileInfo(BaseModel):
    file: Path
    last_modified: int
    filename: str
    size: int | None = None

    @field_serializer('file')
    def serialize_file(self, value):
        return value.resolve().name


def hash_file(file_path: Path, buffer_size: int = 4096) -> str:
    """
    Hash the first buffer_size bytes of a file. This is used to identify if a file was 
    already uploaded.
    :param file_path: The path to the file to hash
    :param buffer_size: The number of bytes to read from the file
    """
    with open(file_path, "rb") as f:
        return hashlib.sha256(f.read(buffer_size)).hexdigest()


def hash_buffer(buffer: bytes, buffer_size: int = 4096) -> str:
    """
    Hash the first buffer_size bytes of a file. This is used to identify if a file was
    already uploaded.
    :param buffer: The buffer to hash
    :param buffer_size: The number of bytes to read from the file
    """
    return hashlib.sha256(buffer[:buffer_size]).hexdigest()



class UploadCache(BaseSettings):
    temporary_directory: Path = Path("/tmp/metacatalog-api")
    data_directory: Path = Path('~').expanduser() / "metacatalog-data"
    buffer_size: int = 4096

    cache: Dict[str, FileInfo] = {}

    def model_post_init(self, __context):
        super().model_post_init(__context)

        # Create directories
        self.temporary_directory.mkdir(parents=True, exist_ok=True)
        self.data_directory.mkdir(parents=True, exist_ok=True)
        
        self.index_cache()
    
    @property
    def metadata_file(self):
        return self.temporary_directory / "metadata.json"
    
    def _save_metadata(self):
        """Save metadata to persistent storage"""
        metadata = {
            hash_:  info.model_dump() for hash_, info in self.cache.items()
        }
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f)
    
    def _load_metadata(self) -> dict:
        """Load metadata from persistent storage"""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
        except json.JSONDecodeError:
            return {}
        return {}

    def index_cache(self):
        """Index temporary directory and load metadata"""
        self.cache = {}
        metadata = self._load_metadata()
        
        for file in self.temporary_directory.glob("*"):
            if file.name == 'metadata.json':
                continue
            file_hash = file.name  # The file name is the hash
            if file_hash in metadata:
                self.cache[file_hash] = FileInfo(**metadata[file_hash])
            else:
                # Handle orphaned files
                self.cache[file_hash] = FileInfo(
                    file=file,
                    last_modified=int(file.stat().st_mtime),
                    filename=f"unknown_{file_hash[:8]}",
                    size=file.stat().st_size
                )
    
    def index_file(self, upload_file: UploadFile):
        # Reset file position after previous read
        upload_file.file.seek(0)
        
        # hash the file
        file_hash = hash_buffer(upload_file.file.read(), self.buffer_size)
        
        # Reset file position for writing
        upload_file.file.seek(0)
        
        # Save file with hash as filename
        temp_path = self.temporary_directory / file_hash
        with open(temp_path, "wb") as f:
            f.write(upload_file.file.read())
        
        # Update cache
        self.cache[file_hash] = FileInfo(
            file=temp_path,
            last_modified=int(datetime.now().timestamp()),
            filename=upload_file.filename,
            size=upload_file.size,
        )
        
        # Save metadata
        self._save_metadata()
        
        return file_hash

    def save_to_data(self, file_hash: str) -> Path:
        """Move file from temporary to data directory"""
        if file_hash not in self.cache:
            raise KeyError(f"File with hash {file_hash} not found in cache")
        
        file_info = self.cache[file_hash]
        original_name = file_info.filename
        
        # Create unique filename in data directory
        target_path = self.data_directory / original_name
        if target_path.exists():
            # If filename exists, append hash to make it unique
            name_parts = original_name.rsplit('.', 1)
            if len(name_parts) > 1:
                new_name = f"{name_parts[0]}_{file_hash[:8]}.{name_parts[1]}"
            else:
                new_name = f"{original_name}_{file_hash[:8]}"
            target_path = self.data_directory / new_name
        
        # Copy file to data directory
        shutil.copy2(file_info.file, target_path)
        self.delete_file(file_hash)
        
        return target_path

    def get_file(self, file_hash: str) -> FileInfo:
        """Return temporary file path and original filename"""
        if file_hash not in self.cache:
            raise KeyError(f"File with hash {file_hash} not found in cache")
        
        return self.cache[file_hash]

    def delete_file(self, file_hash: str):
        """Delete file from temporary storage"""
        if file_hash not in self.cache:
            raise KeyError(f"File with hash {file_hash} not found in cache")
        
        self.cache[file_hash].file.unlink()
        del self.cache[file_hash]
        self._save_metadata()

    def has_file(self, file_hash: str) -> bool:
        """Check if file exists in cache"""
        return file_hash in self.cache
    
    def __contains__(self, file_hash: str) -> bool:
        return self.has_file(file_hash=file_hash)
