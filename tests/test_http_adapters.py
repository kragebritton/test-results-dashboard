from openapi_locustgen.http_adapters import HttpxClient, LocustClient, RequestsClient


class FakeResponse:
    def __init__(self, status_code: int = 200, text: str = "ok"):
        self.status_code = status_code
        self.text = text

    def json(self):
        return {"status": self.status_code}


class RecordingSession:
    def __init__(self, response: FakeResponse):
        self.calls = []
        self._response = response

    def request(self, method, url, **kwargs):  # pragma: no cover - simple recorder
        self.calls.append((method, url, kwargs))
        return self._response


def test_requests_client_combines_base_url_and_forwards_kwargs():
    response = FakeResponse()
    session = RecordingSession(response)
    client = RequestsClient(session, base_url="https://api.example.com")

    returned = client.request("GET", "/pets", headers={"X": "1"}, params={"a": 1})

    assert returned is response
    assert session.calls == [
        (
            "GET",
            "https://api.example.com/pets",
            {"headers": {"X": "1"}, "params": {"a": 1}, "json": None, "data": None},
        )
    ]


def test_httpx_client_joins_url():
    response = FakeResponse(201)
    httpx = RecordingSession(response)
    client = HttpxClient(httpx, base_url="https://service.test/api/")

    returned = client.request("post", "pets", json={"name": "fido"})

    assert returned.status_code == 201
    assert httpx.calls[0][1] == "https://service.test/api/pets"
    assert httpx.calls[0][2]["json"] == {"name": "fido"}


def test_locust_client_prefixes_base_path():
    response = FakeResponse(202)
    locust_session = RecordingSession(response)
    client = LocustClient(locust_session, base_path="/api/v1")

    returned = client.request("DELETE", "pets/1", data="payload")

    assert returned.text == "ok"
    assert locust_session.calls[0][1] == "/api/v1/pets/1"
    assert locust_session.calls[0][2]["data"] == "payload"
