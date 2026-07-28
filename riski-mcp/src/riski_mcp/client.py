"""Async HTTP client for the RISKI backend's non-streaming endpoints (issue #02).

``BackendClient`` covers the read endpoints (``/api/config``, ``/api/healthz``).
The streaming agent endpoint (``/api/ag-ui/riskiagent``) is handled separately in
issue #03 but shares this client's base URL / timeout / header conventions.

Base URL, timeout and auth headers are passed in by the caller; they are wired
to ``Settings`` in issue #05.
"""

from __future__ import annotations

from types import TracebackType
from typing import Self

import httpx

from riski_mcp.models import ConfigResponse, HealthCheckResponse

__all__ = ["BackendClient", "DEFAULT_TIMEOUT_SECONDS"]

DEFAULT_TIMEOUT_SECONDS = 30.0

_CONFIG_PATH = "/api/config"
_HEALTHZ_PATH = "/api/healthz"


class BackendClient:
    """Thin async wrapper over the RISKI backend's non-streaming endpoints.

    Use as an async context manager so the underlying connection pool is closed::

        async with BackendClient("https://backend.example") as client:
            health = await client.healthz()
    """

    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        headers: dict[str, str] | None = None,
        verify: bool = True,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        """Create a backend client.

        Args:
            base_url: Backend root, e.g. ``https://riski.example``. Endpoint
                paths (``/api/...``) are appended to it.
            timeout: Per-request timeout in seconds.
            headers: Extra headers to send on every request (e.g. auth).
            verify: Whether to verify TLS certificates.
            client: Pre-built ``httpx.AsyncClient`` (mainly for tests); when
                given, ``timeout``/``headers``/``verify`` are assumed baked in.
        """
        self._base_url = base_url.rstrip("/")
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            base_url=self._base_url,
            timeout=timeout,
            headers=headers or {},
            verify=verify,
        )

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        """Close the underlying connection pool if this client owns it."""
        if self._owns_client:
            await self._client.aclose()

    async def get_config(self) -> ConfigResponse:
        """Fetch backend configuration from ``GET /api/config``.

        Raises:
            httpx.HTTPStatusError: If the backend returns a non-2xx status.
        """
        response = await self._client.get(_CONFIG_PATH)
        response.raise_for_status()
        return ConfigResponse.model_validate(response.json())

    async def healthz(self) -> HealthCheckResponse:
        """Fetch backend health from ``GET /api/healthz``.

        Raises:
            httpx.HTTPStatusError: If the backend returns a non-2xx status.
        """
        response = await self._client.get(_HEALTHZ_PATH)
        response.raise_for_status()
        return HealthCheckResponse.model_validate(response.json())
