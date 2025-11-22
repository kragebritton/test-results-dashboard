"""Generate Locust user boilerplate that wires in the generated client."""

from __future__ import annotations

from textwrap import dedent


def generate_locust_base_code(
    client_class_name: str = "GeneratedApiClient",
    user_class_name: str = "GeneratedApiUser",
) -> str:
    """Return Python source for the base Locust user that wires in the generated client."""

    return dedent(
        f"""
        from locust import FastHttpUser

        from .client import {client_class_name}
        from .http_adapters import LocustClient


        class {user_class_name}(FastHttpUser):
            def on_start(self):
                http_adapter = LocustClient(self.client)
                self.api = {client_class_name}(http_adapter)


        __all__ = ["{user_class_name}"]
        """
    ).strip()
