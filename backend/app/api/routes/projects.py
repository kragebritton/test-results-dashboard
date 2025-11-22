from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.core.settings import DEFAULT_ENVIRONMENT
from app.models import ProjectRetentionSettings
from app.services.storage import ProjectStorageService

router = APIRouter(prefix="/api", tags=["projects"])


def get_storage_service() -> ProjectStorageService:
    return ProjectStorageService()


@router.get("/projects")
async def list_projects(
    environment: str = DEFAULT_ENVIRONMENT, storage: ProjectStorageService = Depends(get_storage_service)
) -> list[dict[str, object]]:
    environment = storage.validate_environment(environment)
    return storage.list_projects(environment)


@router.get("/overview")
async def project_overview(
    environment: str = DEFAULT_ENVIRONMENT, storage: ProjectStorageService = Depends(get_storage_service)
) -> list[dict[str, object]]:
    environment = storage.validate_environment(environment)
    return storage.project_overview(environment)


@router.get("/projects/{project}")
async def project_details(
    project: str, environment: str = DEFAULT_ENVIRONMENT, storage: ProjectStorageService = Depends(get_storage_service)
) -> dict[str, object]:
    environment = storage.validate_environment(environment)
    return storage.project_details(project, environment)


@router.get("/projects/{project}/retention")
async def get_retention_settings(
    project: str, storage: ProjectStorageService = Depends(get_storage_service)
) -> ProjectRetentionSettings:
    return storage.get_retention_settings(project)


@router.post("/projects/{project}/retention")
async def update_retention_settings(
    project: str, settings: ProjectRetentionSettings, storage: ProjectStorageService = Depends(get_storage_service)
) -> ProjectRetentionSettings:
    return storage.update_retention_settings(project, settings)


@router.post("/projects/{project}/upload")
async def upload_results(
    project: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    environment: str = DEFAULT_ENVIRONMENT,
    storage: ProjectStorageService = Depends(get_storage_service),
) -> dict[str, str]:
    if file.content_type not in {"application/zip", "application/x-zip-compressed", "multipart/form-data"}:
        raise HTTPException(status_code=400, detail="Upload must be a zip archive containing an Allure report.")

    environment = storage.validate_environment(environment)
    build_id = storage.build_id_from_timestamp()
    file_content = await file.read()
    file.file.close()

    background_tasks.add_task(storage.process_upload, project, file_content, build_id, environment)

    return {"message": "Upload accepted", "build_id": build_id}


@router.get("/projects/{project}/report/{path:path}")
async def serve_report(
    project: str,
    path: str = "index.html",
    environment: str = DEFAULT_ENVIRONMENT,
    storage: ProjectStorageService = Depends(get_storage_service),
) -> FileResponse:
    environment = storage.validate_environment(environment)
    safe_path = storage.get_report_path(project, path, environment)
    return FileResponse(safe_path)
