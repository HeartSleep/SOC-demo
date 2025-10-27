"""
Pagination Utilities
Provides pagination helpers for list endpoints
"""
from typing import TypeVar, Generic, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar('T')


class PaginationParams(BaseModel):
    """Pagination parameters for list queries"""
    skip: int = Field(default=0, ge=0, description="Number of records to skip")
    limit: int = Field(default=50, ge=1, le=100, description="Maximum number of records to return")

    @property
    def offset(self) -> int:
        """Get offset for database queries"""
        return self.skip


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response"""
    items: List[T] = Field(description="List of items")
    total: int = Field(description="Total number of items")
    skip: int = Field(description="Number of items skipped")
    limit: int = Field(description="Maximum items per page")
    has_more: bool = Field(description="Whether there are more items")

    @property
    def page(self) -> int:
        """Current page number (1-indexed)"""
        return (self.skip // self.limit) + 1

    @property
    def total_pages(self) -> int:
        """Total number of pages"""
        return (self.total + self.limit - 1) // self.limit


async def paginate_query(
    db: AsyncSession,
    query,
    pagination: PaginationParams,
    count_query = None
) -> PaginatedResponse:
    """
    Paginate a SQLAlchemy query.

    Args:
        db: Database session
        query: SQLAlchemy select query
        pagination: Pagination parameters
        count_query: Optional count query (defaults to query without pagination)

    Returns:
        PaginatedResponse with items and metadata
    """
    # Get total count
    if count_query is None:
        # Extract the main entity from the query
        count_query = select(func.count()).select_from(query.subquery())

    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Apply pagination to main query
    paginated_query = query.offset(pagination.offset).limit(pagination.limit)
    result = await db.execute(paginated_query)
    items = result.scalars().all()

    return PaginatedResponse(
        items=items,
        total=total,
        skip=pagination.skip,
        limit=pagination.limit,
        has_more=(pagination.skip + len(items)) < total
    )


def get_pagination_params(skip: int = 0, limit: int = 50) -> PaginationParams:
    """
    Create pagination parameters with validation.

    Args:
        skip: Number of records to skip (default: 0)
        limit: Maximum records to return (default: 50, max: 100)

    Returns:
        PaginationParams object

    Example:
        @router.get("/items")
        async def list_items(
            pagination: PaginationParams = Depends(get_pagination_params),
            db: AsyncSession = Depends(get_session)
        ):
            query = select(Item).order_by(Item.created_at.desc())
            return await paginate_query(db, query, pagination)
    """
    return PaginationParams(skip=skip, limit=limit)


class CursorPaginationParams(BaseModel):
    """Cursor-based pagination parameters for efficient large dataset pagination"""
    cursor: Optional[str] = Field(default=None, description="Cursor for next page")
    limit: int = Field(default=50, ge=1, le=100, description="Maximum number of records to return")


class CursorPaginatedResponse(BaseModel, Generic[T]):
    """Generic cursor-paginated response"""
    items: List[T] = Field(description="List of items")
    next_cursor: Optional[str] = Field(description="Cursor for next page")
    has_more: bool = Field(description="Whether there are more items")
    limit: int = Field(description="Maximum items per page")


# Convenience functions for common pagination patterns
def get_default_pagination() -> PaginationParams:
    """Get default pagination (skip=0, limit=50)"""
    return PaginationParams(skip=0, limit=50)


def get_large_pagination() -> PaginationParams:
    """Get large pagination (skip=0, limit=100)"""
    return PaginationParams(skip=0, limit=100)


def get_small_pagination() -> PaginationParams:
    """Get small pagination (skip=0, limit=20)"""
    return PaginationParams(skip=0, limit=20)