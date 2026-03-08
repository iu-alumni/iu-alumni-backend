import base64
import json
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Paginated(BaseModel, Generic[T]):
    items: list[T]
    next_cursor: str | None = None


def encode_cursor(data: dict) -> str:
    return base64.b64encode(json.dumps(data, default=str).encode()).decode()


def decode_cursor(cursor: str) -> dict:
    return json.loads(base64.b64decode(cursor.encode()).decode())
