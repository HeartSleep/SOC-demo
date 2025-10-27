"""
Standardized API Response Models
Ensures consistent response format across all endpoints
"""

from typing import Generic, TypeVar, List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated response format"""
    items: List[T]
    total: int
    page: int
    size: int
    pages: int

    class Config:
        schema_extra = {
            "example": {
                "items": [],
                "total": 100,
                "page": 1,
                "size": 20,
                "pages": 5
            }
        }


class StandardResponse(BaseModel, Generic[T]):
    """Standard single item response"""
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    timestamp: datetime = datetime.now()

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": {},
                "message": "Operation completed successfully",
                "timestamp": "2025-09-28T12:00:00"
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response format"""
    success: bool = False
    error: str
    detail: Optional[str] = None
    status_code: int
    timestamp: datetime = datetime.now()

    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "error": "Resource not found",
                "detail": "The requested asset does not exist",
                "status_code": 404,
                "timestamp": "2025-09-28T12:00:00"
            }
        }


class BulkOperationResponse(BaseModel):
    """Response for bulk operations"""
    success: bool = True
    total: int
    succeeded: int
    failed: int
    errors: List[Dict[str, Any]] = []
    results: List[Dict[str, Any]] = []
    timestamp: datetime = datetime.now()

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "total": 10,
                "succeeded": 8,
                "failed": 2,
                "errors": [
                    {"id": "1", "error": "Validation failed"},
                    {"id": "2", "error": "Duplicate entry"}
                ],
                "results": [],
                "timestamp": "2025-09-28T12:00:00"
            }
        }


def create_paginated_response(
    items: List[Any],
    total: int,
    page: int,
    size: int
) -> Dict[str, Any]:
    """
    Helper function to create consistent paginated responses

    Args:
        items: List of items for current page
        total: Total number of items
        page: Current page number (1-indexed)
        size: Items per page

    Returns:
        Standardized paginated response dictionary
    """
    pages = (total + size - 1) // size if size > 0 else 0

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }


def create_success_response(
    data: Any = None,
    message: str = "Operation completed successfully"
) -> Dict[str, Any]:
    """
    Helper function to create success responses

    Args:
        data: Response data
        message: Success message

    Returns:
        Standardized success response dictionary
    """
    return {
        "success": True,
        "data": data,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }


def create_error_response(
    error: str,
    status_code: int,
    detail: Optional[str] = None
) -> Dict[str, Any]:
    """
    Helper function to create error responses

    Args:
        error: Error message
        status_code: HTTP status code
        detail: Additional error details

    Returns:
        Standardized error response dictionary
    """
    return {
        "success": False,
        "error": error,
        "detail": detail,
        "status_code": status_code,
        "timestamp": datetime.now().isoformat()
    }