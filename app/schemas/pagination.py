from base64 import b64decode, b64encode
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
