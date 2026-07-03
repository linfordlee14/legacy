"""Cursor pagination (API_SPECIFICATION 4.1).

Lists return {"data": [...], "next_cursor": "..." | null}. Cursors are
opaque: base64 of the last row's time-ordered id. limit defaults to 25 and
never exceeds 100 (validated at the parameter layer).
"""

import base64
import binascii
import uuid
from typing import Annotated, Any

from fastapi import Query
from pydantic import BaseModel

from legacy_api.api.errors import ApiError, ErrorCode

DEFAULT_LIMIT = 25
MAX_LIMIT = 100

LimitParam = Annotated[int, Query(ge=1, le=MAX_LIMIT)]
CursorParam = Annotated[str | None, Query()]


class Page(BaseModel):
    data: list[dict[str, Any]]  # rows are serialized resource objects
    next_cursor: str | None


def encode_cursor(last_id: str) -> str:
    return base64.urlsafe_b64encode(last_id.encode()).decode()


def decode_cursor(cursor: str) -> str:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
        uuid.UUID(raw)
    except (binascii.Error, ValueError, UnicodeDecodeError):
        raise ApiError(
            422, ErrorCode.VALIDATION_FAILED, "Invalid cursor.", {"param": "cursor"}
        ) from None
    return raw


def page_of(rows: list[dict[str, Any]], limit: int, id_key: str = "id") -> Page:
    """Build a page from limit+1 fetched rows: the extra row signals more."""
    has_more = len(rows) > limit
    visible = rows[:limit]
    next_cursor = encode_cursor(str(visible[-1][id_key])) if has_more and visible else None
    return Page(data=visible, next_cursor=next_cursor)
