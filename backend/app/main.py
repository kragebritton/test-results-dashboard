from __future__ import annotations

import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PROJECTS_DIR = DATA_DIR / "projects"
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "static"
METADATA_FILENAME = "metadata.json"

app = FastAPI(title="Test Results Dashboard API", openapi_url="/api/openapi.json")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HistoryEntry(BaseModel):
    build_id: str
    uploaded_at: datetime


class ProjectMetadata(BaseModel):
    project: str
    latest: Optional[str] = None
    history: List[HistoryEntry] = Field(default_factory=list)

    def save(self) -> None:
        project_dir = PROJECTS_DIR / self.project
        project_dir.mkdir(parents=True, exist_ok=True)
        metadata_path = project_dir / METADATA_FILENAME
        with metadata_path.open("w", encoding="utf-8") as fp:
            fp.write(self.model_dump_json(indent=2))

    @classmethod
    def load(cls, project: str) -> "ProjectMetadata":
        metadata_path = PROJECTS_DIR / project / METADATA_FILENAME
        if metadata_path.exists():
            return cls.model_validate_json(metadata_path.read_text(encoding="utf-8"))
        return cls(project=project)


def ensure_directories() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)


@app.on_event("startup")
async def startup_event() -> None:
    ensure_directories()


@app.get("/api/projects")
async def list_projects() -> list[dict[str, object]]:
    ensure_directories()
    projects = []
    for project_dir in PROJECTS_DIR.iterdir():
        if not project_dir.is_dir():
            continue
        metadata = ProjectMetadata.load(project_dir.name)
        projects.append(
            {
                "project": project_dir.name,
                "latest": metadata.latest,
                "history": metadata.history,
                "reportUrl": f"/api/projects/{project_dir.name}/report/index.html" if metadata.latest else None,
            }
        )
    return sorted(projects, key=lambda item: item["project"])


@app.get("/api/projects/{project}")
async def project_details(project: str) -> dict[str, object]:
    metadata = ProjectMetadata.load(project)
    if metadata.latest is None:
        raise HTTPException(status_code=404, detail="Project has no uploaded reports yet.")

    return {
        "project": project,
        "latest": metadata.latest,
        "history": metadata.history,
        "reportUrl": f"/api/projects/{project}/report/index.html",
    }


def _extract_upload(project: str, upload: UploadFile, build_id: str) -> Path:
    project_dir = PROJECTS_DIR / project
    history_dir = project_dir / "history"
    history_dir.mkdir(parents=True, exist_ok=True)

    target_dir = history_dir / build_id
    if target_dir.exists():
        shutil.rmtree(target_dir)

    with tempfile.TemporaryDirectory() as temp_dir:
        tmp_path = Path(temp_dir) / "upload.zip"
        with tmp_path.open("wb") as buffer:
            shutil.copyfileobj(upload.file, buffer)

        with tempfile.TemporaryDirectory() as extract_dir:
            with zipfile.ZipFile(tmp_path, "r") as archive:
                archive.extractall(extract_dir)

            shutil.copytree(extract_dir, target_dir)

    return target_dir


@app.post("/api/projects/{project}/upload")
async def upload_results(project: str, background_tasks: BackgroundTasks, file: UploadFile = File(...)) -> dict[str, str]:
    ensure_directories()
    if file.content_type not in {"application/zip", "application/x-zip-compressed", "multipart/form-data"}:
        raise HTTPException(status_code=400, detail="Upload must be a zip archive containing an Allure report.")

    build_id = datetime.utcnow().strftime("%Y%m%d%H%M%S")

    def process_upload() -> None:
        try:
            report_dir = _extract_upload(project, file, build_id)
            index_path = report_dir / "index.html"
            if not index_path.exists():
                raise HTTPException(
                    status_code=400,
                    detail="Uploaded archive does not contain an Allure report (index.html missing).",
                )

            metadata = ProjectMetadata.load(project)
            metadata.latest = build_id
            metadata.history.append(HistoryEntry(build_id=build_id, uploaded_at=datetime.utcnow()))
            metadata.save()
        finally:
            file.file.close()

    background_tasks.add_task(process_upload)

    return {"message": "Upload accepted", "build_id": build_id}


def _safe_join(base: Path, path: Path) -> Path:
    try:
        resolved = path.resolve()
        base_resolved = base.resolve()
        if base_resolved in resolved.parents or resolved == base_resolved:
            return resolved
    except RuntimeError:
        pass
    raise HTTPException(status_code=404, detail="File not found")


@app.get("/api/projects/{project}/report/{path:path}")
async def serve_report(project: str, path: str = "index.html") -> FileResponse:
    metadata = ProjectMetadata.load(project)
    if metadata.latest is None:
        raise HTTPException(status_code=404, detail="Project not found or no report uploaded.")

    report_dir = PROJECTS_DIR / project / "history" / metadata.latest
    if not report_dir.exists():
        raise HTTPException(status_code=404, detail="Report not found.")

    requested_path = report_dir / path
    if requested_path.is_dir():
        requested_path = requested_path / "index.html"

    safe_path = _safe_join(report_dir, requested_path)

    if not safe_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(safe_path)


if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
else:

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"status": "ok", "message": "Test Results Dashboard API"}
