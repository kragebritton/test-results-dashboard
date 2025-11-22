from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app.models import HistoryEntry, ProjectMetadata
from app.services.storage import ProjectStorageService


def test_validate_environment_rejects_invalid_value(storage_service: ProjectStorageService):
    with pytest.raises(Exception) as excinfo:
        storage_service.validate_environment("qa")
    assert "Unsupported environment" in str(excinfo.value)


def test_build_id_from_timestamp_is_stable(storage_service: ProjectStorageService):
    timestamp = datetime(2024, 1, 2, 3, 4, 5)
    assert storage_service.build_id_from_timestamp(timestamp) == "20240102030405"


def test_cleanup_project_history_applies_retention(storage_service: ProjectStorageService, temp_projects_dir):
    project = "demo"
    old_entry = HistoryEntry(
        build_id="old-build",
        uploaded_at=datetime.utcnow() - timedelta(days=10),
        environment="prod",
    )
    new_entry = HistoryEntry(
        build_id="new-build",
        uploaded_at=datetime.utcnow(),
        environment="prod",
    )
    metadata = ProjectMetadata(
        project=project,
        latest="new-build",
        latest_by_environment={"prod": "new-build"},
        history=[old_entry, new_entry],
        retention_runs=1,
    )

    for entry in metadata.history:
        (temp_projects_dir / project / "history" / entry.environment / entry.build_id).mkdir(parents=True)

    removed = storage_service.cleanup_project_history(metadata)

    assert removed is True
    assert metadata.history == [new_entry]
    assert metadata.latest == "new-build"
    assert metadata.latest_by_environment == {"prod": "new-build"}
    assert not (temp_projects_dir / project / "history" / "prod" / "old-build").exists()
