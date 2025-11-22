from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

import httpx
import pytest

from app.api.routes import projects as projects_routes
from app.core import settings
from app.main import create_application
from app.services.storage import ProjectStorageService


@pytest.fixture()
def temp_projects_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    data_dir = tmp_path / "data"
    projects_dir = data_dir / "projects"

    monkeypatch.setattr(settings, "DATA_DIR", data_dir)
    monkeypatch.setattr(settings, "PROJECTS_DIR", projects_dir)

    # Keep the storage module in sync with the patched settings paths.
    import app.services.storage as storage

    monkeypatch.setattr(storage, "PROJECTS_DIR", projects_dir)
    monkeypatch.setattr(storage, "DATA_DIR", data_dir)
    monkeypatch.setattr(storage, "ensure_directories", settings.ensure_directories)

    settings.ensure_directories()
    return projects_dir


@pytest.fixture()
def storage_service(temp_projects_dir: Path) -> ProjectStorageService:
    return ProjectStorageService(projects_dir=temp_projects_dir)


@pytest.fixture()
def app(storage_service: ProjectStorageService):
    application = create_application()
    application.dependency_overrides[projects_routes.get_storage_service] = lambda: storage_service

    yield application

    application.dependency_overrides.clear()


@pytest.fixture()
async def async_client(app) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
