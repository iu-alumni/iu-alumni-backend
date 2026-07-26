from base64 import b64decode, b64encode
from datetime import datetime
from json import dumps, loads
from typing import Generic, TypeVar

from pydantic import BaseModel


T = TypeVar("T")


class Paginated(BaseModel, Generic[T]):
    items: list[T]
    next_cursor: str | None = None


def encode_cursor(data: dict) -> str:
    return b64encode(dumps(data, default=str).encode()).decode()


def decode_cursor(cursor: str) -> dict:
    return loads(b64decode(cursor.encode()).decode())


def cursor_datetime(value: str | datetime) -> datetime:
    """Turn a cursor's timestamp back into a real ``datetime``.

    Cursors are JSON, so `encode_cursor` serialises datetimes with `str()` and
    they come back as text. Comparing a DateTime column against that raw string
    only works where the driver happens to coerce it, so keyset pagination that
    relies on it is silently wrong on other backends. Parse it explicitly
    instead — `str(datetime)` and `datetime.isoformat()` are both accepted by
    `fromisoformat`.
    """
    return value if isinstance(value, datetime) else datetime.fromisoformat(value)
