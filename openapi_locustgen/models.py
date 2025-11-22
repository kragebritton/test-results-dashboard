from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class Parameter:
    name: str
    in_: str  # "path", "query", etc.
    required: bool
    schema: Dict[str, Any]
    example: Any | None = None


@dataclass
class RequestBody:
    content_type: str
    schema: Dict[str, Any]
    example: Any | None = None


@dataclass
class Response:
    status_code: int
    description: str
    content: Dict[str, Any]


@dataclass
class Operation:
    operation_id: str
    method: str
    path: str
    summary: str | None
    parameters: List[Parameter]
    request_body: Optional[RequestBody]
    responses: Dict[int, Response]


@dataclass
class OpenApiDocument:
    title: str
    version: str
    operations: List[Operation]
