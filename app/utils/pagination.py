import math
from typing import Any, Dict, List
from app.schemas.pagination import PaginationParams


def get_paginated_response(
    items: List[Any], total: int, pagination: PaginationParams
) -> Dict[str, Any]:
    """
    Creates a standardized dictionary for paginated data based on the items, total count,
    and pagination parameters.
    """
    last_page = math.ceil(total / pagination.size) if total > 0 else 1
    current_page = pagination.page
    next_page = current_page + 1 if current_page < last_page else None
    prev_page = current_page - 1 if current_page > 1 else None
    from_item = (current_page - 1) * pagination.size + 1 if total > 0 else 0
    to_item = min(current_page * pagination.size, total) if total > 0 else 0

    return {
        "items": items,
        "pagination": {
            "total": total,
            "current_page": current_page,
            "last_page": last_page,
            "next_page": next_page,
            "prev_page": prev_page,
            "from": from_item,
            "to": to_item,
        },
    }
