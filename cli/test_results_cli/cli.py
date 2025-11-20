from __future__ import annotations

import tempfile
import zipfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import httpx
import typer

app = typer.Typer(help="Upload test result archives to the Test Results Dashboard API.")


@contextmanager
def _prepare_archive(report_path: Path) -> Iterator[Path]:
    """
    Normalize the report path into a zip archive.

    If the path is already a zip file, use it directly. Otherwise, zip the
    directory contents into a temporary archive.
    """

    if not report_path.exists():
        raise typer.BadParameter(f"Path not found: {report_path}")

    if report_path.is_file():
        if not zipfile.is_zipfile(report_path):
            raise typer.BadParameter("When providing a file, it must be a zip archive containing the report.")
        yield report_path
        return

    with tempfile.TemporaryDirectory() as temp_dir:
        archive_path = Path(temp_dir) / "report.zip"
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for file_path in report_path.rglob("*"):
                if file_path.is_file():
                    archive.write(file_path, file_path.relative_to(report_path))
        yield archive_path


@app.command()
def upload(
    report_path: Path = typer.Argument(
        ..., help="Path to an Allure report directory or an existing zip archive of the report."
    ),
    project: str = typer.Option(..., "--project", "-p", help="Project name to upload the report for."),
    api_url: str = typer.Option(
        "http://localhost:8000/api", "--api-url", help="Base API URL for the Test Results Dashboard backend."
    ),
    timeout: float = typer.Option(30.0, help="HTTP timeout (in seconds) for the upload request."),
) -> None:
    """Package and upload a test results report to the dashboard backend."""

    endpoint = f"{api_url.rstrip('/')}/projects/{project}/upload"
    typer.echo(f"Preparing archive from: {report_path}")

    with _prepare_archive(report_path) as archive_path:
        typer.echo(f"Uploading to: {endpoint}")
        with archive_path.open("rb") as fp:
            files = {"file": ("report.zip", fp, "application/zip")}
            try:
                response = httpx.post(endpoint, files=files, timeout=timeout)
            except httpx.RequestError as exc:
                raise typer.Exit(code=1) from typer.BadParameter(f"Failed to reach API: {exc}")

    if response.is_success:
        message = response.json().get("message", "Upload succeeded")
        build_id = response.json().get("build_id")
        typer.secho(f"{message} (build_id={build_id})", fg=typer.colors.GREEN)
    else:
        try:
            detail = response.json().get("detail")
        except ValueError:
            detail = response.text
        typer.secho(f"Upload failed ({response.status_code}): {detail}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
