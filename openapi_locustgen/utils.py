from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import yaml

from .models import OpenApiDocument, Operation, Parameter, RequestBody, Response


ALLOWED_METHODS = {"get", "post", "put", "delete"}


def _coerce_status_code(status: str) -> int:
    try:
        return int(status)
    except (TypeError, ValueError):
        raise ValueError(f"Unsupported status code value: {status}") from None


def _build_operation_id(method: str, path: str) -> str:
    sanitized = path.strip("/").replace("/", "_").replace("{", "").replace("}", "")
    sanitized = sanitized or "root"
    return f"{method.lower()}_{sanitized}"


def _parse_parameters(raw_parameters: List[Dict[str, Any]]) -> List[Parameter]:
    parameters: List[Parameter] = []
    for param in raw_parameters:
        name = param.get("name")
        location = param.get("in")
        if not name or not location:
            continue
        parameters.append(
            Parameter(
                name=name,
                in_=location,
                required=bool(param.get("required", False)),
                schema=param.get("schema", {}),
                example=param.get("example"),
            )
        )
    return parameters


def _parse_request_body(raw_body: Dict[str, Any] | None) -> RequestBody | None:
    if not raw_body:
        return None
    content = raw_body.get("content", {})
    if not content:
        return None
    # Prefer application/json if present, otherwise pick the first content type
    content_type = "application/json" if "application/json" in content else next(iter(content))
    media_type = content.get(content_type, {})
    schema = media_type.get("schema", {})
    example = media_type.get("example") or raw_body.get("example")
    return RequestBody(content_type=content_type, schema=schema, example=example)


def _parse_responses(raw_responses: Dict[str, Any]) -> Dict[int, Response]:
    responses: Dict[int, Response] = {}
    for status, resp in raw_responses.items():
        code = _coerce_status_code(status)
        description = resp.get("description", "")
        content = resp.get("content", {})
        responses[code] = Response(status_code=code, description=description, content=content)
    return responses


def load_openapi(path: str) -> OpenApiDocument:
    """Load an OpenAPI spec from a file and convert to :class:`OpenApiDocument`."""

    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"OpenAPI file not found: {path}")

    text = file_path.read_text(encoding="utf-8")
    if file_path.suffix.lower() == ".json":
        raw_spec = json.loads(text)
    else:
        raw_spec = yaml.safe_load(text)

    info = raw_spec.get("info", {})
    title = info.get("title", "")
    version = info.get("version", "")

    operations: List[Operation] = []
    paths = raw_spec.get("paths", {})
    for path_name, path_item in paths.items():
        path_parameters = _parse_parameters(path_item.get("parameters", [])) if isinstance(path_item, dict) else []
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method.lower() not in ALLOWED_METHODS:
                continue
            if not isinstance(operation, dict):
                continue
            op_parameters = path_parameters + _parse_parameters(operation.get("parameters", []))
            request_body = _parse_request_body(operation.get("requestBody"))
            responses = _parse_responses(operation.get("responses", {}))
            operation_id = operation.get("operationId") or _build_operation_id(method, path_name)
            operations.append(
                Operation(
                    operation_id=operation_id,
                    method=method.upper(),
                    path=path_name,
                    summary=operation.get("summary"),
                    parameters=op_parameters,
                    request_body=request_body,
                    responses=responses,
                )
            )

    return OpenApiDocument(title=title, version=version, operations=operations)
