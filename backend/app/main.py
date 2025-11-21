from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes.projects import router as projects_router
from app.core.settings import FRONTEND_DIST, ensure_directories


def create_application() -> FastAPI:
    application = FastAPI(title="Test Results Dashboard API", openapi_url="/api/openapi.json")

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(projects_router)

    @application.on_event("startup")
    async def startup_event() -> None:  # pragma: no cover - startup hook
        ensure_directories()

    if FRONTEND_DIST.exists():
        application.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
    else:

        @application.get("/")
        async def root() -> dict[str, str]:
            return {"status": "ok", "message": "Test Results Dashboard API"}

    return application


app = create_application()
