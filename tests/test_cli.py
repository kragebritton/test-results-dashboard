from __future__ import annotations

from pathlib import Path

from openapi_locustgen import cli


def test_cli_generates_client_and_locust_files(tmp_path: Path):
    spec_path = Path(__file__).parent / "data" / "simple_openapi.yaml"
    out_dir = tmp_path / "generated_api"

    cli.main(
        [
            "--spec",
            str(spec_path),
            "--out",
            str(out_dir),
            "--client-class",
            "PetsClient",
            "--user-class",
            "PetsUser",
        ]
    )

    client_file = out_dir / "client.py"
    locust_file = out_dir / "locust_base.py"
    init_file = out_dir / "__init__.py"

    assert client_file.exists()
    assert locust_file.exists()
    assert init_file.exists()

    client_text = client_file.read_text(encoding="utf-8")
    locust_text = locust_file.read_text(encoding="utf-8")

    assert "class PetsClient" in client_text
    assert "class PetsUser" in locust_text
    assert "from .client import PetsClient" in init_file.read_text(encoding="utf-8")
