from __future__ import annotations

import sys
import types

from openapi_locustgen.codegen.locust_codegen import generate_locust_base_code


class DummyHttpClient:
    def __init__(self):
        self.requested = False

    def request(self, *args, **kwargs):
        self.requested = True
        return types.SimpleNamespace(status_code=200, text="ok")


def test_locust_user_wires_generated_client(monkeypatch):
    locust_module = types.ModuleType("locust")

    class FastHttpUser:
        def __init__(self):
            self.client = DummyHttpClient()

    locust_module.FastHttpUser = FastHttpUser
    monkeypatch.setitem(sys.modules, "locust", locust_module)

    package = types.ModuleType("generated")
    package.__path__ = []
    monkeypatch.setitem(sys.modules, "generated", package)

    class GeneratedApiClient:
        def __init__(self, http):
            self.http = http

    client_module = types.ModuleType("generated.client")
    client_module.GeneratedApiClient = GeneratedApiClient
    monkeypatch.setitem(sys.modules, "generated.client", client_module)

    class LocustClient:
        def __init__(self, client):
            self._client = client

    adapters_module = types.ModuleType("generated.http_adapters")
    adapters_module.LocustClient = LocustClient
    monkeypatch.setitem(sys.modules, "generated.http_adapters", adapters_module)

    namespace = {"__name__": "generated.locust_base", "__package__": "generated"}
    src = generate_locust_base_code()
    exec(src, namespace)

    UserClass = namespace["GeneratedApiUser"]
    user = UserClass()
    user.on_start()

    assert hasattr(user, "api")
    assert isinstance(user.api, GeneratedApiClient)
    assert isinstance(user.api.http._client, DummyHttpClient)
