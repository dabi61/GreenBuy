from typing import TypeVar, Generic, List, Optional
from pydantic import BaseModel
from sqlmodel import Session, select, func
from sqlalchemy import Select

T = TypeVar('T')

class PaginationParams(BaseModel):
    page: int = 1
    limit: int = 10
    search: Optional[str] = None
    sort_by: Optional[str] = None
    sort_order: str = "asc"  # asc or desc

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool

def paginate(
    session: Session,
    query: Select,
    params: PaginationParams
) -> PaginatedResponse:
    """
    Utility function để thực hiện phân trang cho bất kỳ query nào
    """
    # Đếm tổng số records
    count_query = select(func.count()).select_from(query.subquery())
    total = session.exec(count_query).one()
    
    # Tính toán offset
    offset = (params.page - 1) * params.limit
    
    # Apply pagination
    paginated_query = query.offset(offset).limit(params.limit)
    items = session.exec(paginated_query).all()
    
    # Tính toán metadata
    total_pages = (total + params.limit - 1) // params.limit
    has_next = params.page < total_pages
    has_prev = params.page > 1
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=params.page,
        limit=params.limit,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev
    ) 