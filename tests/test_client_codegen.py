from __future__ import annotations

import sys
import types
from types import SimpleNamespace

from openapi_locustgen.codegen.client_codegen import generate_client_code
from openapi_locustgen.models import OpenApiDocument, Operation, Parameter, RequestBody


class FakeResponse(SimpleNamespace):
    def json(self):
        return getattr(self, "_json", None)


class RecordingHttpClient:
    def __init__(self):
        self.calls: list[tuple] = []

    def request(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return FakeResponse(status_code=200, text="ok")


def _build_doc() -> OpenApiDocument:
    path_param = Parameter(name="pet_id", in_="path", required=True, schema={})
    query_param = Parameter(name="limit", in_="query", required=False, schema={})
    body = RequestBody(content_type="application/json", schema={})

    get_op = Operation(
        operation_id="get_pet",
        method="GET",
        path="/pets/{pet_id}",
        summary="Get a pet",
        parameters=[path_param, query_param],
        request_body=None,
        responses={},
    )
    post_op = Operation(
        operation_id="create_pet",
        method="POST",
        path="/pets",
        summary="Create a pet",
        parameters=[],
        request_body=body,
        responses={},
    )
    return OpenApiDocument(title="Pets", version="1.0", operations=[get_op, post_op])


def test_generated_client_executes_operations():
    doc = _build_doc()
    src = generate_client_code(doc)
    package = types.ModuleType("generated")
    package.__path__ = []
    sys.modules["generated"] = package

    http_module = types.ModuleType("generated.http_adapters")

    class HttpClient:
        pass

    class HttpResponse:
        pass

    http_module.HttpClient = HttpClient
    http_module.HttpResponse = HttpResponse
    sys.modules["generated.http_adapters"] = http_module

    namespace: dict[str, object] = {"__name__": "generated.client", "__package__": "generated"}
    exec(src, namespace)

    ClientClass = namespace["GeneratedApiClient"]
    http = RecordingHttpClient()
    client = ClientClass(http)

    client.get_pet(123)
    client.get_pet(123, limit=10)
    client.create_pet(body={"name": "fido"})

    first_args, first_kwargs = http.calls[0]
    assert first_args[0] == "GET"
    assert first_args[1] == "/pets/123"
    assert first_kwargs["params"] is None

    _, second_kwargs = http.calls[1]
    assert second_kwargs["params"] == {"limit": 10}

    third_args, third_kwargs = http.calls[2]
    assert third_args[0] == "POST"
    assert third_kwargs["json"] == {"name": "fido"}
