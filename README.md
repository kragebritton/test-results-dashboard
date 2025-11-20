# Test Results Dashboard

A small FastAPI + React application for ingesting and browsing Allure reports by project.

## Features

- **API ingestion**: Upload zipped Allure reports and pin them to a project; the service stores history and exposes the latest report per project.
- **Project directory**: Quickly browse available projects and their latest build identifiers.
- **Embedded Allure**: The front-end renders the latest report within an iframe while also providing a link to open it in a new tab.

## Getting started

### Backend (FastAPI)

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

The backend now uses [uv](https://github.com/astral-sh/uv) with dependencies declared in `backend/pyproject.toml` and resolved via `uv lock`/`uv sync`.

### Frontend (Vite + React)

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api` requests to `localhost:8000` so the UI and API work together during development.

### Uploading Allure reports

Send a zipped Allure report to the upload endpoint. The archive must include `index.html` at its root.

```bash
curl -X POST "http://localhost:8000/api/projects/my-project/upload" \
  -H "Content-Type: application/zip" \
  --data-binary @allure-report.zip
```

After the upload completes, browse to the front-end, select the project, and the latest Allure report will appear in the embedded viewer.
