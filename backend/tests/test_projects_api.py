from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime

import pytest

from app.core import settings
from app.models import HistoryEntry, ProjectMetadata
from app.services.storage import ProjectStorageService


def _build_allure_archive() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("index.html", "<html>Report</html>")
        archive.writestr(
            "widgets/summary.json",
            json.dumps({"statistic": {"passed": 3, "failed": 1, "broken": 0, "skipped": 0, "total": 4}}),
        )
    buffer.seek(0)
    return buffer.read()


@pytest.mark.asyncio
async def test_list_projects_returns_empty(async_client):
    response = await async_client.get("/api/projects")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_project_overview_includes_summary(async_client, storage_service: ProjectStorageService, temp_projects_dir):
    metadata = ProjectMetadata(
        project="demo",
        latest="build-001",
        latest_by_environment={"prod": "build-001"},
        history=[HistoryEntry(build_id="build-001", uploaded_at=datetime(2024, 1, 1), environment="prod")],
        retention_runs=5,
    )
    storage_service.save_metadata(metadata)

    summary_path = temp_projects_dir / "demo" / "history" / "prod" / "build-001" / "widgets"
    summary_path.mkdir(parents=True, exist_ok=True)
    summary_path.joinpath(settings.SUMMARY_FILENAME).write_text(
        json.dumps({"statistic": {"passed": 2, "failed": 0, "broken": 0, "skipped": 0, "total": 2}}),
        encoding="utf-8",
    )

    response = await async_client.get("/api/overview")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    overview = body[0]
    assert overview["project"] == "demo"
    assert overview["status"] == "passed"
    assert overview["statistics"]["passed"] == 2
    assert overview["reportUrl"].endswith("environment=prod")


@pytest.mark.asyncio
async def test_project_details_missing_returns_404(async_client):
    response = await async_client.get("/api/projects/unknown")
    assert response.status_code == 404
    assert response.json()["detail"] == "Project has no uploaded reports yet."


@pytest.mark.asyncio
async def test_upload_and_serve_report(async_client, storage_service: ProjectStorageService, monkeypatch):
    archive = _build_allure_archive()
    monkeypatch.setattr(storage_service, "build_id_from_timestamp", lambda timestamp=None: "build-xyz")

    response = await async_client.post(
        "/api/projects/sample-project/upload?environment=staging",
        files={"file": ("report.zip", archive, "application/zip")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["build_id"] == "build-xyz"
    assert payload["message"] == "Upload accepted"

    metadata = storage_service.load_metadata("sample-project")
    assert metadata.latest == "build-xyz"
    assert metadata.latest_by_environment == {"staging": "build-xyz"}
    assert metadata.history[0].environment == "staging"

    report_response = await async_client.get(
        "/api/projects/sample-project/report/index.html?environment=staging"
    )
    assert report_response.status_code == 200
    assert "<html>Report</html>" in report_response.text


@pytest.mark.asyncio
async def test_upload_rejects_non_zip(async_client):
    response = await async_client.post(
        "/api/projects/project-1/upload",
        files={"file": ("report.txt", b"not a zip", "text/plain")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Upload must be a zip archive containing an Allure report."
