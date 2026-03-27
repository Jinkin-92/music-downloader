"""
Download History API Router

Provides endpoints for download history management:
- GET /api/history - Get all history records
- POST /api/history/verify - Verify file status
- DELETE /api/history/clean - Clean missing records
- POST /api/history/open-folder - Open folder in file explorer
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

from backend.services.history_service import history_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix='/api/history',
    tags=['下载历史']
)


# ==================== Pydantic Models ====================

class OpenFolderRequest(BaseModel):
    """Open folder request"""
    file_path: str


class HistoryStatsResponse(BaseModel):
    """History statistics response"""
    total: int
    valid: int
    missing: int


class CleanResponse(BaseModel):
    """Clean missing records response"""
    success: bool
    deleted_count: int


class OpenFolderResponse(BaseModel):
    """Open folder response"""
    success: bool
    message: str


class DeleteRecordResponse(BaseModel):
    """Delete history record response"""
    success: bool
    message: str


# ==================== API Endpoints ====================

@router.get('')
async def get_history():
    """
    Get all download history records

    Returns:
        List of history records with file status
    """
    try:
        records = history_service.get_all_history(include_missing=True)
        logger.info(f"[History] Retrieved {len(records)} records")
        return {
            'success': True,
            'total': len(records),
            'records': records
        }
    except Exception as e:
        logger.error(f"[History] Failed to get history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/verify', response_model=HistoryStatsResponse)
async def verify_files():
    """
    Verify all files exist and update status

    Returns:
        Statistics: total, valid, missing counts
    """
    try:
        stats = history_service.get_stats()
        logger.info(f"[History] Verified files: {stats}")
        return HistoryStatsResponse(**stats)
    except Exception as e:
        logger.error(f"[History] Failed to verify files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete('/clean', response_model=CleanResponse)
async def clean_missing_records():
    """
    Clean records for missing files

    Returns:
        Number of deleted records
    """
    try:
        deleted_count = history_service.clean_missing_records()
        logger.info(f"[History] Cleaned {deleted_count} missing records")
        return CleanResponse(
            success=True,
            deleted_count=deleted_count
        )
    except Exception as e:
        logger.error(f"[History] Failed to clean records: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/open-folder', response_model=OpenFolderResponse)
async def open_folder(request: OpenFolderRequest):
    """
    Open folder in file explorer

    Args:
        request: File path to open

    Returns:
        Success status
    """
    try:
        success = history_service.open_folder(request.file_path)
        if success:
            logger.info(f"[History] Opened folder: {request.file_path}")
            return OpenFolderResponse(
                success=True,
                message='Folder opened successfully'
            )
        else:
            return OpenFolderResponse(
                success=False,
                message='File not found or cannot open folder'
            )
    except Exception as e:
        logger.error(f"[History] Failed to open folder: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/stats', response_model=HistoryStatsResponse)
async def get_stats():
    """
    Get download history statistics

    Returns:
        Statistics: total, valid, missing counts
    """
    try:
        stats = history_service.get_stats()
        return HistoryStatsResponse(**stats)
    except Exception as e:
        logger.error(f"[History] Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete('/{record_id}', response_model=DeleteRecordResponse)
async def delete_record(record_id: int, delete_file: bool = False):
    """
    Delete a history record, optionally deleting the local file too.

    Args:
        record_id: History record ID
        delete_file: Whether to remove the file from disk as well

    Returns:
        Success status
    """
    try:
        success = history_service.delete_file_and_record(record_id, delete_file=delete_file)
        if not success:
            raise HTTPException(status_code=404, detail='记录不存在')

        action = '记录和文件' if delete_file else '记录'
        logger.info(f"[History] Deleted {action}: id={record_id}")
        return DeleteRecordResponse(
            success=True,
            message=f'已删除{action}'
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[History] Failed to delete record {record_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
