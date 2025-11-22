"""Command-line interface for generating clients and Locust scaffolding."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .codegen.client_codegen import generate_client_code
from .codegen.locust_codegen import generate_locust_base_code
from .utils import load_openapi


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate API client and Locust scaffolding")
    parser.add_argument("--spec", "-s", required=True, help="Path to OpenAPI 3.x spec (YAML or JSON)")
    parser.add_argument("--out", "-o", required=True, help="Output directory for generated package")
    parser.add_argument("--client-class", default="GeneratedApiClient", help="Client class name")
    parser.add_argument("--user-class", default="GeneratedApiUser", help="Locust user class name")
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    doc = load_openapi(args.spec)
    out_dir = Path(args.out)

    client_code = generate_client_code(doc, class_name=args.client_class)
    locust_code = generate_locust_base_code(
        client_class_name=args.client_class, user_class_name=args.user_class
    )

    _write_file(out_dir / "client.py", client_code + "\n")
    _write_file(out_dir / "locust_base.py", locust_code + "\n")
    init_content = "\n".join(
        [
            f"from .client import {args.client_class}",
            f"from .locust_base import {args.user_class}",
            "",
            f"__all__ = ['{args.client_class}', '{args.user_class}']",
            "",
        ]
    )
    _write_file(out_dir / "__init__.py", init_content)


if __name__ == "__main__":
    main()
