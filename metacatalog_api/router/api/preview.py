from pathlib import Path
import mimetypes
import csv
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import text

from metacatalog_api import core
from metacatalog_api import models
from datetime import datetime, timedelta
import re
from pydantic import BaseModel
from typing import Any
import polars as pl


# Preview response models
class VariableInfo(BaseModel):
    """Information about a variable/column in the dataset"""
    name: str
    column_index: int
    datatype: str  # e.g., "numeric", "string", "datetime", "boolean"
    sample_values: list[str] | None = None
    has_numeric: bool | None = None
    has_dates: bool | None = None


class FilePreviewResponse(BaseModel):
    """Response model for file preview endpoints"""
    file_hash: str
    file_size: int
    mimetype: str
    encoding: str
    
    # Variable information
    variables: list[VariableInfo]
    
    # Data dimensionality
    rows: int | None = None
    columns: int | None = None
    shape: list[int] | None = None
    
    # Spatial and temporal scales (if detected)
    spatial_scale: models.SpatialScaleBase | None = None
    temporal_scale: models.TemporalScaleBase | None = None
    
    # Additional inferred metadata
    inferred_metadata: dict[str, Any] = {}
    
    # File-specific analysis results
    analysis_details: dict[str, Any] = {}


preview_router = APIRouter()


# Dependency injection for file objects
async def get_file_from_hash(file_hash: str) -> Path:
    """Dependency to get file path from hash"""
    if not core.cache.has_file(file_hash):
        raise HTTPException(status_code=404, detail=f"File with hash {file_hash} not found")
    
    file_info = core.cache.get_file(file_hash)
    return file_info.file


# Base analysis functions
def analyze_csv_file(file_path: Path, max_rows: int = 1000) -> Dict[str, Any]:
    """Analyze a CSV file using Polars and return detailed metadata"""
    try:
        # Try to read with Polars - it handles delimiter detection automatically
        # Use more lenient parsing for quoted fields and handle quoted strings
        df = pl.read_csv(
            file_path, 
            n_rows=max_rows, 
            ignore_errors=True,
            quote_char='"',
            null_values=["", "null", "NULL"]
        )
        
        if df.height == 0:
            return {"error": "Empty CSV file"}
        
        # Get basic info
        total_rows = df.height
        total_columns = df.width
        headers = df.columns
        
        # Analyze each column
        column_analysis = []
        temporal_columns = []
        spatial_columns = []
        
        for i, col_name in enumerate(headers):
            col_data = df[col_name]
            
            # Get sample values (first 3 non-null values)
            sample_values = col_data.drop_nulls().head(3).to_list()
            sample_values = [str(v) for v in sample_values]
            
            # Determine data type based on Polars dtype
            datatype = "string"
            has_numeric = False
            has_dates = False
            
            dtype = col_data.dtype
            
            # Check if column is numeric
            if dtype in [pl.Int64, pl.Float64, pl.Int32, pl.Float32]:
                datatype = "numeric"
                has_numeric = True
            # Check if column is datetime
            elif dtype == pl.Datetime:
                datatype = "datetime"
                has_dates = True
                temporal_columns.append(i)
            # Check if column contains dates (string format)
            elif dtype == pl.Utf8:
                # Try to parse as dates
                try:
                    # Try to parse as datetime
                    parsed_dates = pl.Series(col_data.drop_nulls()).str.to_datetime()
                    datatype = "datetime"
                    has_dates = True
                    temporal_columns.append(i)
                except:
                    # Try to parse as numeric
                    try:
                        pl.Series(col_data.drop_nulls()).cast(pl.Float64)
                        datatype = "numeric"
                        has_numeric = True
                    except:
                        datatype = "string"
            
            # Check for spatial columns (common names)
            spatial_keywords = ['lat', 'latitude', 'lon', 'longitude', 'x', 'y', 'coord']
            if any(keyword in col_name.lower() for keyword in spatial_keywords):
                spatial_columns.append(i)
            
            column_analysis.append({
                "name": col_name,
                "index": i,
                "datatype": datatype,
                "sample_values": sample_values,
                "has_numeric": has_numeric,
                "has_dates": has_dates
            })
        
        # Detect temporal scale
        temporal_scale = None
        if temporal_columns:
            try:
                for col_idx in temporal_columns:
                    col_name = headers[col_idx]
                    col_data = df[col_name]
                    
                    # Convert to datetime if not already
                    if col_data.dtype != pl.Datetime:
                        col_data = col_data.str.to_datetime()
                    
                    # Get min/max dates
                    valid_dates = col_data.drop_nulls()
                    if valid_dates.height > 0:
                        min_date = valid_dates.min().item()
                        max_date = valid_dates.max().item()
                        
                        temporal_scale = {
                            "observation_start": min_date,
                            "observation_end": max_date,
                            "resolution": timedelta(days=1),  # Default to daily
                            "support": 1.0,
                            "dimension_names": [col_name]
                        }
                        break  # Use first temporal column found
            except Exception:
                pass
        
        # Detect spatial scale
        spatial_scale = None
        if len(spatial_columns) >= 2:
            try:
                # Find lat/lon columns
                lat_col = None
                lon_col = None
                
                for col_idx in spatial_columns:
                    col_name = headers[col_idx].lower()
                    if any(keyword in col_name for keyword in ['lat', 'latitude']):
                        lat_col = col_idx
                    elif any(keyword in col_name for keyword in ['lon', 'longitude']):
                        lon_col = col_idx
                
                if lat_col is not None and lon_col is not None:
                    # Get lat/lon data
                    lat_data = df[headers[lat_col]].cast(pl.Float64).drop_nulls()
                    lon_data = df[headers[lon_col]].cast(pl.Float64).drop_nulls()
                    
                    if lat_data.height > 0 and lon_data.height > 0:
                        spatial_scale = {
                            "resolution": 1,  # Default resolution
                            "support": 1.0,
                            "dimension_names": [headers[lat_col], headers[lon_col]]
                        }
            except Exception:
                pass
        
        return {
            "file_type": "csv",
            "delimiter": ",",  # Polars handles this automatically
            "headers": headers,
            "column_analysis": column_analysis,
            "total_rows": total_rows,
            "total_columns": total_columns,
            "encoding": "utf-8",
            "temporal_scale": temporal_scale,
            "spatial_scale": spatial_scale,
            "temporal_columns": temporal_columns,
            "spatial_columns": spatial_columns
        }
    except Exception as e:
        return {"error": f"Failed to analyze CSV: {str(e)}"}


def analyze_netcdf_file(file_path: Path) -> Dict[str, Any]:
    """Analyze a netCDF file and return metadata"""
    try:
        # This would require netCDF4 library
        # For now, return basic info
        return {
            "file_type": "netcdf",
            "error": "netCDF analysis not yet implemented",
            "note": "Requires netCDF4 library for full analysis"
        }
    except Exception as e:
        return {"error": f"Failed to analyze netCDF: {str(e)}"}


def analyze_text_file(file_path: Path) -> Dict[str, Any]:
    """Analyze a text file and return metadata"""
    try:
        sample_content = []
        total_lines = 0
        total_chars = 0
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                total_lines += 1
                total_chars += len(line)
                if i < 5:  # First 5 lines
                    sample_content.append(line.strip())
        
        return {
            "file_type": "text",
            "sample_content": sample_content,
            "total_lines": total_lines,
            "total_chars": total_chars,
            "encoding": "utf-8"
        }
    except Exception as e:
        return {"error": f"Failed to analyze text file: {str(e)}"}


def analyze_generic_file(file_path: Path) -> Dict[str, Any]:
    """Analyze a generic file and return basic metadata"""
    try:
        mime_type, _ = mimetypes.guess_type(str(file_path))
        
        return {
            "file_type": "generic",
            "mime_type": mime_type or "application/octet-stream",
            "file_extension": file_path.suffix.lower(),
            "encoding": "utf-8"
        }
    except Exception as e:
        return {"error": f"Failed to analyze file: {str(e)}"}


# Factory function to create preview response from analysis
def create_preview_response(analysis: Dict[str, Any], file_hash: str, file_path: Path) -> FilePreviewResponse:
    """Create a FilePreviewResponse object from analysis results"""
    
    # Get file info
    file_info = core.cache.get_file(file_hash)
    file_size = file_info.size if file_info else 0
    
    # Detect mimetype
    detected_mime, _ = mimetypes.guess_type(str(file_path))
    if detected_mime is None:
        detected_mime = "application/octet-stream"
    
    # Build variable information
    variables = []
    if analysis.get("column_analysis"):
        for col in analysis["column_analysis"]:
            variables.append(VariableInfo(
                name=col["name"],
                column_index=col["index"],
                datatype=col["datatype"],
                sample_values=col.get("sample_values"),
                has_numeric=col.get("has_numeric"),
                has_dates=col.get("has_dates")
            ))
    elif analysis.get("headers"):
        # For cases where we have headers but no detailed analysis
        for i, header in enumerate(analysis["headers"]):
            variables.append(VariableInfo(
                name=header,
                column_index=i,
                datatype="string",
                sample_values=None,
                has_numeric=None,
                has_dates=None
            ))
    
    # Build inferred metadata
    inferred_metadata = {}
    if analysis.get("delimiter"):
        inferred_metadata["delimiter"] = analysis["delimiter"]
    if analysis.get("temporal_columns"):
        inferred_metadata["temporal_columns"] = analysis["temporal_columns"]
    if analysis.get("spatial_columns"):
        inferred_metadata["spatial_columns"] = analysis["spatial_columns"]
    
    # Create response
    response = FilePreviewResponse(
        file_hash=file_hash,
        file_size=file_size,
        mimetype=detected_mime,
        encoding=analysis.get("encoding", "utf-8"),
        variables=variables,
        rows=analysis.get("total_rows") or analysis.get("total_lines"),
        columns=analysis.get("total_columns"),
        shape=None,  # For future multi-dimensional data
        spatial_scale=analysis.get("spatial_scale"),
        temporal_scale=analysis.get("temporal_scale"),
        inferred_metadata=inferred_metadata,
        analysis_details=analysis
    )
    
    return response


# CSV Preview Endpoint
@preview_router.get('/csv/{file_hash}')
async def get_csv_preview(file_path: Path = Depends(get_file_from_hash)) -> FilePreviewResponse:
    """
    Analyze a file as CSV and return detailed preview information.
    
    This endpoint treats any file as CSV, regardless of its actual mimetype.
    Useful for files that are CSV but have different extensions.
    """
    try:
        analysis = analyze_csv_file(file_path)
        file_hash = file_path.name  # The filename is the hash
        
        if "error" in analysis:
            raise HTTPException(status_code=400, detail=analysis["error"])
        
        response = create_preview_response(analysis, file_hash, file_path)
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze CSV file: {str(e)}")


# NetCDF Preview Endpoint
@preview_router.get('/netcdf/{file_hash}')
async def get_netcdf_preview(file_path: Path = Depends(get_file_from_hash)) -> FilePreviewResponse:
    """
    Analyze a file as NetCDF and return detailed preview information.
    
    This endpoint treats any file as NetCDF, regardless of its actual mimetype.
    """
    try:
        analysis = analyze_netcdf_file(file_path)
        file_hash = file_path.name  # The filename is the hash
        
        if "error" in analysis:
            raise HTTPException(status_code=400, detail=analysis["error"])
        
        response = create_preview_response(analysis, file_hash, file_path)
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze NetCDF file: {str(e)}")


# Text Preview Endpoint
@preview_router.get('/text/{file_hash}')
async def get_text_preview(file_path: Path = Depends(get_file_from_hash)) -> FilePreviewResponse:
    """
    Analyze a file as text and return detailed preview information.
    
    This endpoint treats any file as text, regardless of its actual mimetype.
    """
    try:
        analysis = analyze_text_file(file_path)
        file_hash = file_path.name  # The filename is the hash
        
        if "error" in analysis:
            raise HTTPException(status_code=400, detail=analysis["error"])
        
        response = create_preview_response(analysis, file_hash, file_path)
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze text file: {str(e)}")


# Generic Preview Endpoint
@preview_router.get('/generic/{file_hash}')
async def get_generic_preview(file_path: Path = Depends(get_file_from_hash)) -> FilePreviewResponse:
    """
    Analyze a file generically and return detailed preview information.
    
    This endpoint provides basic file analysis for any file type.
    """
    try:
        analysis = analyze_generic_file(file_path)
        file_hash = file_path.name  # The filename is the hash
        
        if "error" in analysis:
            raise HTTPException(status_code=400, detail=analysis["error"])
        
        response = create_preview_response(analysis, file_hash, file_path)
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze file: {str(e)}")


# Auto-detection endpoint (for backward compatibility)
@preview_router.get('/auto/{file_hash}')
async def get_auto_preview(file_path: Path = Depends(get_file_from_hash)) -> FilePreviewResponse:
    """
    Automatically detect file type and return detailed preview information.
    
    This endpoint tries to guess the file type based on extension and content.
    """
    try:
        file_extension = file_path.suffix.lower()
        file_hash = file_path.name
        
        # Auto-detect based on extension
        if file_extension == '.csv':
            analysis = analyze_csv_file(file_path)
        elif file_extension in ['.nc', '.netcdf', '.cdf']:
            analysis = analyze_netcdf_file(file_path)
        elif file_extension in ['.txt', '.md', '.log']:
            analysis = analyze_text_file(file_path)
        else:
            analysis = analyze_generic_file(file_path)
        
        if "error" in analysis:
            raise HTTPException(status_code=400, detail=analysis["error"])
        
        response = create_preview_response(analysis, file_hash, file_path)
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze file: {str(e)}")
