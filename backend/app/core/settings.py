from __future__ import annotations

from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PROJECTS_DIR = DATA_DIR / "projects"
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "static"
METADATA_FILENAME = "metadata.json"
SUMMARY_FILENAME = "summary.json"


def ensure_directories() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
