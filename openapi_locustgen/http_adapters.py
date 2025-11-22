"""HTTP client protocols and adapters."""

from __future__ import annotations

from typing import Any, Mapping, Protocol


class HttpResponse(Protocol):
    """Minimal response interface shared by supported HTTP clients."""

    status_code: int
    text: str

    def json(self) -> Any: ...


class HttpClient(Protocol):
    """Protocol describing the minimal HTTP surface required by generated clients."""

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        params: Mapping[str, Any] | None = None,
        json: Any | None = None,
        data: Any | None = None,
    ) -> HttpResponse: ...


def _combine_url(base: str | None, path: str) -> str:
    base = (base or "").rstrip("/")
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{base}{path}" if base else path


class RequestsClient:
    """Adapter for ``requests.Session``-compatible clients."""

    def __init__(self, session: Any, *, base_url: str | None = None):
        self._session = session
        self._base_url = base_url

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        params: Mapping[str, Any] | None = None,
        json: Any | None = None,
        data: Any | None = None,
    ) -> HttpResponse:
        full_url = _combine_url(self._base_url, url)
        return self._session.request(
            method,
            full_url,
            headers=headers,
            params=params,
            json=json,
            data=data,
        )


class HttpxClient:
    """Adapter for ``httpx.Client``-compatible clients."""

    def __init__(self, client: Any, *, base_url: str | None = None):
        self._client = client
        self._base_url = base_url

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        params: Mapping[str, Any] | None = None,
        json: Any | None = None,
        data: Any | None = None,
    ) -> HttpResponse:
        full_url = _combine_url(self._base_url, url)
        return self._client.request(
            method,
            full_url,
            headers=headers,
            params=params,
            json=json,
            data=data,
        )


class LocustClient:
    """Adapter for Locust ``HttpSession`` or ``FastHttpUser.client``."""

    def __init__(self, client: Any, *, base_path: str | None = None):
        self._client = client
        self._base_path = base_path

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        params: Mapping[str, Any] | None = None,
        json: Any | None = None,
        data: Any | None = None,
    ) -> HttpResponse:
        full_url = _combine_url(self._base_path, url)
        return self._client.request(
            method,
            full_url,
            headers=headers,
            params=params,
            json=json,
            data=data,
        )


__all__ = [
    "HttpClient",
    "HttpResponse",
    "RequestsClient",
    "HttpxClient",
    "LocustClient",
]
