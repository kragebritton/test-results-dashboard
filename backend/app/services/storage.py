from __future__ import annotations

import json
import shutil
import tempfile
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import HTTPException

from app.core.settings import (
    ALLOWED_ENVIRONMENTS,
    DEFAULT_ENVIRONMENT,
    METADATA_FILENAME,
    PROJECTS_DIR,
    SUMMARY_FILENAME,
    ensure_directories,
)
from app.models import HistoryEntry, ProjectMetadata, ProjectRetentionSettings


class ProjectStorageService:
    def __init__(self, projects_dir: Path = PROJECTS_DIR) -> None:
        self.projects_dir = projects_dir
        ensure_directories()

    @staticmethod
    def validate_environment(environment: str) -> str:
        if environment not in ALLOWED_ENVIRONMENTS:
            raise HTTPException(status_code=400, detail="Unsupported environment specified.")
        return environment

    @staticmethod
    def _latest_for_environment(metadata: ProjectMetadata, environment: str) -> str | None:
        if metadata.latest_by_environment.get(environment):
            return metadata.latest_by_environment[environment]

        if environment == DEFAULT_ENVIRONMENT and metadata.latest and not metadata.latest_by_environment:
            return metadata.latest

        return None

    @staticmethod
    def _history_for_environment(metadata: ProjectMetadata, environment: str) -> list[HistoryEntry]:
        if not metadata.history:
            return []

        scoped_history = [entry for entry in metadata.history if entry.environment == environment]
        if scoped_history:
            return scoped_history

        if environment == DEFAULT_ENVIRONMENT:
            return metadata.history

        return []

    # Metadata helpers
    def load_metadata(self, project: str) -> ProjectMetadata:
        metadata_path = self.projects_dir / project / METADATA_FILENAME
        if metadata_path.exists():
            return ProjectMetadata.model_validate_json(metadata_path.read_text(encoding="utf-8"))
        return ProjectMetadata(project=project)

    def save_metadata(self, metadata: ProjectMetadata) -> None:
        project_dir = self.projects_dir / metadata.project
        project_dir.mkdir(parents=True, exist_ok=True)
        metadata_path = project_dir / METADATA_FILENAME
        with metadata_path.open("w", encoding="utf-8") as fp:
            fp.write(metadata.model_dump_json(indent=2))

    # Summary helpers
    def _summary_path(self, project: str, environment: str, build_id: str) -> Path:
        return self.projects_dir / project / "history" / environment / build_id / "widgets" / SUMMARY_FILENAME

    def _legacy_summary_path(self, project: str, build_id: str) -> Path:
        return self.projects_dir / project / "history" / build_id / "widgets" / SUMMARY_FILENAME

    def _load_summary_statistics(self, project: str, build_id: str, environment: str) -> dict[str, int]:
        base_stats = {
            "passed": 0,
            "failed": 0,
            "broken": 0,
            "skipped": 0,
            "unknown": 0,
            "total": 0,
        }

        summary_path = self._summary_path(project, environment, build_id)
        legacy_summary_path = self._legacy_summary_path(project, build_id)

        if not summary_path.exists() and legacy_summary_path.exists():
            summary_path = legacy_summary_path
        if not summary_path.exists():
            return base_stats

        try:
            summary_data = json.loads(summary_path.read_text(encoding="utf-8"))
            statistic = summary_data.get("statistic") or {}
        except (json.JSONDecodeError, OSError):
            return base_stats

        stats: dict[str, int] = base_stats.copy()
        for key in stats:
            if key == "total":
                continue
            stats[key] = int(statistic.get(key, 0))

        stats["total"] = int(statistic.get("total", sum(stats.values())))
        return stats

    @staticmethod
    def _derive_status(statistics: dict[str, int]) -> str:
        if statistics["failed"] > 0 or statistics["broken"] > 0:
            return "failed"
        if statistics["passed"] > 0 and statistics["failed"] == 0 and statistics["broken"] == 0:
            return "passed"
        return "unknown"

    @staticmethod
    def _last_run_for_project(metadata: ProjectMetadata, environment: str) -> datetime | None:
        if metadata.latest is None:
            return None

        for entry in reversed(metadata.history):
            if entry.environment != environment:
                continue
            if entry.build_id == metadata.latest_by_environment.get(environment, metadata.latest):
                return entry.uploaded_at
        return None

    # Listing endpoints
    def list_projects(self, environment: str = DEFAULT_ENVIRONMENT) -> list[dict[str, object]]:
        ensure_directories()
        projects: list[dict[str, object]] = []
        for project_dir in self.projects_dir.iterdir():
            if not project_dir.is_dir():
                continue
            metadata = self.load_metadata(project_dir.name)
            latest_id = self._latest_for_environment(metadata, environment)
            projects.append(
                {
                    "project": project_dir.name,
                    "latest": latest_id,
                    "environment": environment,
                    "history": self._history_for_environment(metadata, environment),
                    "retentionRuns": metadata.retention_runs,
                    "retentionDays": metadata.retention_days,
                    "reportUrl": self._build_report_url(project_dir.name, latest_id, environment),
                }
            )
        return sorted(projects, key=lambda item: item["project"])

    def project_overview(self, environment: str = DEFAULT_ENVIRONMENT) -> list[dict[str, object]]:
        ensure_directories()
        overview: list[dict[str, object]] = []

        for project_dir in self.projects_dir.iterdir():
            if not project_dir.is_dir():
                continue

            metadata = self.load_metadata(project_dir.name)
            latest_id = self._latest_for_environment(metadata, environment)
            statistics = (
                self._load_summary_statistics(project_dir.name, latest_id, environment)
                if latest_id
                else {
                    "passed": 0,
                    "failed": 0,
                    "broken": 0,
                    "skipped": 0,
                    "unknown": 0,
                    "total": 0,
                }
            )

            overview.append(
                {
                    "project": project_dir.name,
                    "latest": latest_id,
                    "environment": environment,
                    "lastRun": self._last_run_for_project(metadata, environment),
                    "status": self._derive_status(statistics),
                    "statistics": statistics,
                    "retentionRuns": metadata.retention_runs,
                    "retentionDays": metadata.retention_days,
                    "reportUrl": self._build_report_url(project_dir.name, latest_id, environment),
                }
            )

        return sorted(overview, key=lambda item: item["project"])

    # Retention
    def cleanup_project_history(self, metadata: ProjectMetadata) -> bool:
        if metadata.retention_runs is None and metadata.retention_days is None:
            return False

        project_dir = self.projects_dir / metadata.project
        history_dir = project_dir / "history"
        if not history_dir.exists():
            return False

        now = datetime.utcnow()
        entries = sorted(metadata.history, key=lambda entry: entry.uploaded_at, reverse=True)

        retained: list[HistoryEntry] = []
        for entry in entries:
            if metadata.retention_days is not None and entry.uploaded_at < now - timedelta(days=metadata.retention_days):
                continue
            retained.append(entry)

        if metadata.retention_runs is not None:
            retained = retained[: metadata.retention_runs]

        retained_keys = {(entry.environment, entry.build_id) for entry in retained}
        removed_entries = [entry for entry in entries if (entry.environment, entry.build_id) not in retained_keys]
        for entry in removed_entries:
            target_dir = history_dir / entry.environment / entry.build_id
            legacy_dir = history_dir / entry.build_id
            if target_dir.exists():
                shutil.rmtree(target_dir, ignore_errors=True)
            elif legacy_dir.exists():
                shutil.rmtree(legacy_dir, ignore_errors=True)

        latest_id = metadata.latest
        if latest_id and latest_id not in {entry.build_id for entry in retained}:
            metadata.latest = retained[0].build_id if retained else None

        metadata.history = retained
        for env, build_id in list(metadata.latest_by_environment.items()):
            env_history = [entry for entry in retained if entry.environment == env]
            if env_history:
                metadata.latest_by_environment[env] = env_history[0].build_id
            else:
                metadata.latest_by_environment.pop(env, None)

        return bool(removed_entries or latest_id != metadata.latest)

    # Upload handling
    def process_upload(self, project: str, upload_content: bytes, build_id: str, environment: str) -> None:
        try:
            report_dir = self._extract_upload(project, upload_content, build_id, environment)
            index_path = report_dir / "index.html"
            if not index_path.exists():
                raise HTTPException(
                    status_code=400,
                    detail="Uploaded archive does not contain an Allure report (index.html missing).",
                )

            metadata = self.load_metadata(project)
            metadata.latest = build_id
            metadata.latest_by_environment[environment] = build_id
            metadata.history.append(
                HistoryEntry(build_id=build_id, uploaded_at=datetime.utcnow(), environment=environment)
            )
            self.cleanup_project_history(metadata)
            self.save_metadata(metadata)
        finally:
            # No open file handles are held, but this keeps the contract symmetrical with upload caller.
            pass

    def _extract_upload(self, project: str, upload_content: bytes, build_id: str, environment: str) -> Path:
        project_dir = self.projects_dir / project
        history_dir = project_dir / "history" / environment
        history_dir.mkdir(parents=True, exist_ok=True)

        target_dir = history_dir / build_id
        if target_dir.exists():
            shutil.rmtree(target_dir)

        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir) / "upload.zip"
            with tmp_path.open("wb") as buffer:
                buffer.write(upload_content)

            with tempfile.TemporaryDirectory() as extract_dir:
                with zipfile.ZipFile(tmp_path, "r") as archive:
                    archive.extractall(extract_dir)

                shutil.copytree(extract_dir, target_dir)

        return target_dir

    # Report serving
    def safe_join(self, base: Path, path: Path) -> Path:
        try:
            resolved = path.resolve()
            base_resolved = base.resolve()
            if base_resolved in resolved.parents or resolved == base_resolved:
                return resolved
        except RuntimeError:
            pass
        raise HTTPException(status_code=404, detail="File not found")

    def get_report_path(self, project: str, path: str, environment: str) -> Path:
        metadata = self.load_metadata(project)
        latest_id = self._latest_for_environment(metadata, environment)
        if latest_id is None:
            raise HTTPException(status_code=404, detail="Project not found or no report uploaded.")

        report_dir = self.projects_dir / project / "history" / environment / latest_id
        legacy_report_dir = self.projects_dir / project / "history" / latest_id
        if not report_dir.exists() and legacy_report_dir.exists():
            report_dir = legacy_report_dir

        if not report_dir.exists():
            raise HTTPException(status_code=404, detail="Report not found.")

        requested_path = report_dir / path
        if requested_path.is_dir():
            requested_path = requested_path / "index.html"

        safe_path = self.safe_join(report_dir, requested_path)

        if not safe_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        return safe_path

    # Retention endpoints
    def get_retention_settings(self, project: str) -> ProjectRetentionSettings:
        metadata = self.load_metadata(project)
        return ProjectRetentionSettings(
            retention_runs=metadata.retention_runs, retention_days=metadata.retention_days
        )

    def update_retention_settings(self, project: str, settings: ProjectRetentionSettings) -> ProjectRetentionSettings:
        ensure_directories()
        metadata = self.load_metadata(project)
        metadata.retention_runs = settings.retention_runs
        metadata.retention_days = settings.retention_days

        self.cleanup_project_history(metadata)
        self.save_metadata(metadata)

        return ProjectRetentionSettings(
            retention_runs=metadata.retention_runs, retention_days=metadata.retention_days
        )

    # Details endpoints
    def project_details(self, project: str, environment: str = DEFAULT_ENVIRONMENT) -> dict[str, object]:
        metadata = self.load_metadata(project)
        latest_id = self._latest_for_environment(metadata, environment)
        if latest_id is None:
            raise HTTPException(status_code=404, detail="Project has no uploaded reports yet.")

        return {
            "project": project,
            "latest": latest_id,
            "environment": environment,
            "history": self._history_for_environment(metadata, environment),
            "retentionRuns": metadata.retention_runs,
            "retentionDays": metadata.retention_days,
            "reportUrl": self._build_report_url(project, latest_id, environment),
        }

    # Utility
    @staticmethod
    def _build_report_url(project: str, latest: str | None, environment: str) -> str | None:
        if latest:
            return f"/api/projects/{project}/report/index.html?environment={environment}"
        return None

    @staticmethod
    def build_id_from_timestamp(timestamp: datetime | None = None) -> str:
        return (timestamp or datetime.utcnow()).strftime("%Y%m%d%H%M%S")


__all__ = ["ProjectStorageService"]
