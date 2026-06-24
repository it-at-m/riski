"""Tests for the non-streaming BackendClient (issue #02)."""

from __future__ import annotations

import httpx
import pytest
import respx
from riski_mcp.client import BackendClient

BASE_URL = "https://backend.test"

_CONFIG_BODY = {
    "version": "v1.2.3",
    "frontend_version": "v4.5.6",
    "title": "RISKI",
    "documentation_url": "https://docs.example",
    "contact_url": "https://contact.example",
    "impressum_url": "https://impressum.example",
    "townhallbulletin_url": "https://bulletin.example",
}


@respx.mock
async def test_get_config() -> None:
    route = respx.get(f"{BASE_URL}/api/config").mock(return_value=httpx.Response(200, json=_CONFIG_BODY))

    async with BackendClient(BASE_URL) as client:
        config = await client.get_config()

    assert route.called
    assert config.version == "v1.2.3"
    assert config.title == "RISKI"


@respx.mock
async def test_healthz() -> None:
    route = respx.get(f"{BASE_URL}/api/healthz").mock(return_value=httpx.Response(200, json={"status": "ok", "version": "v0.1.0"}))

    async with BackendClient(BASE_URL) as client:
        health = await client.healthz()

    assert route.called
    assert health.status == "ok"
    assert health.version == "v0.1.0"


@respx.mock
async def test_trailing_slash_base_url_normalized() -> None:
    respx.get(f"{BASE_URL}/api/healthz").mock(return_value=httpx.Response(200, json={"version": "v0.1.0"}))

    async with BackendClient(f"{BASE_URL}/") as client:
        health = await client.healthz()

    assert health.status == "ok"  # default applied


@respx.mock
async def test_custom_headers_sent() -> None:
    route = respx.get(f"{BASE_URL}/api/healthz").mock(return_value=httpx.Response(200, json={"version": "v0.1.0"}))

    async with BackendClient(BASE_URL, headers={"Authorization": "Bearer secret"}) as client:
        await client.healthz()

    assert route.calls.last.request.headers["Authorization"] == "Bearer secret"


@respx.mock
async def test_non_2xx_raises() -> None:
    respx.get(f"{BASE_URL}/api/config").mock(return_value=httpx.Response(503))

    async with BackendClient(BASE_URL) as client:
        with pytest.raises(httpx.HTTPStatusError):
            await client.get_config()
