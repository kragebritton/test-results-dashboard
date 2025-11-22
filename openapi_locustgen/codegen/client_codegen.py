"""Generate a thin Python API client from an :class:`OpenApiDocument`."""

from __future__ import annotations

from textwrap import indent
from typing import Iterable

from ..models import OpenApiDocument, Operation, Parameter


def _build_method_signature(op: Operation) -> str:
    path_params = [p for p in op.parameters if p.in_ == "path"]
    query_params = [p for p in op.parameters if p.in_ == "query"]

    parts: list[str] = ["self"]
    for param in path_params + query_params:
        default = "" if param.required else " = None"
        parts.append(f"{param.name}{default}")

    if op.request_body:
        parts.append("body: dict | None = None")

    return ", ".join(parts)


def _format_path(path: str) -> str:
    """Return an f-string literal for a templated path like ``/pets/{id}``."""

    return f"f\"{path}\""


def _build_query_params(query_params: Iterable[Parameter]) -> list[str]:
    params_list = list(query_params)
    lines: list[str] = []
    if not params_list:
        return ["params = None"]

    lines.append("params = {}")
    for param in params_list:
        name = param.name
        lines.append(f"if {name} is not None:")
        lines.append(f"    params[\"{name}\"] = {name}")
    lines.append("if not params:")
    lines.append("    params = None")
    return lines


def _build_request_call(op: Operation) -> str:
    args = [f"\"{op.method}\"", "path"]
    args.append("params=params")
    if op.request_body:
        args.append("json=body")
    else:
        args.append("json=None")
    return f"return self._http.request({', '.join(args)})"


def _generate_method(op: Operation) -> str:
    signature = _build_method_signature(op)
    path_literal = _format_path(op.path)
    query_params = [p for p in op.parameters if p.in_ == "query"]

    lines: list[str] = []
    lines.append(f"def {op.operation_id}({signature}):")
    summary = op.summary or ""
    lines.append(f'    """{summary}"""')
    lines.append(f"    path = {path_literal}")
    for line in _build_query_params(query_params):
        lines.append(f"    {line}")
    lines.append(f"    {_build_request_call(op)}")
    return "\n".join(lines)


def generate_client_code(doc: OpenApiDocument, class_name: str = "GeneratedApiClient") -> str:
    """
    Return Python source code for a client class implementing one method per operation.
    """

    method_blocks = [_generate_method(op) for op in doc.operations]
    methods_src = "\n\n".join(method_blocks)
    methods_src = indent(methods_src, "    ") if methods_src else ""

    return "\n".join(
        [
            "from __future__ import annotations",
            "",
            "from typing import Any",
            "",
            "from .http_adapters import HttpClient, HttpResponse",
            "",
            "",
            f"class {class_name}:",
            "    def __init__(self, http: HttpClient):",
            "        self._http = http",
            "",
            methods_src,
        ]
    ).strip()
