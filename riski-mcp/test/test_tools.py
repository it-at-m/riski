"""Tests for the MCP tool functions (issue #04)."""

from __future__ import annotations

import json
from collections.abc import Iterator

import httpx
import pytest
import respx
from riski_mcp.config import get_settings
from riski_mcp.tools import get_riski_capabilities, search_munich_ris

BASE_URL = "https://backend.test"
AGENT_URL = f"{BASE_URL}/api/ag-ui/riskiagent"


@pytest.fixture
def configured(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Configure a backend URL and reset the cached settings around the test."""
    monkeypatch.setenv("RISKI_MCP__BACKEND_URL", BASE_URL)
    monkeypatch.setenv("RISKI_MCP__MAX_SOURCES", "3")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _sse_answer() -> bytes:
    structured = json.dumps(
        {
            "response": "Es gibt Anträge zum Radverkehr.",
            "documents": [{"name": "Beschlussvorlage Radwege"}],
            "proposals": [],
        }
    )
    events = [
        {"type": "TEXT_MESSAGE_START", "messageId": "m1"},
        {"type": "TEXT_MESSAGE_CONTENT", "messageId": "m1", "delta": structured},
        {"type": "TEXT_MESSAGE_END", "messageId": "m1"},
        {"type": "RUN_FINISHED"},
    ]
    return "".join(f"data: {json.dumps(e)}\n\n" for e in events).encode("utf-8")


@respx.mock
async def test_search_munich_ris_end_to_end(configured: None) -> None:
    respx.post(AGENT_URL).mock(return_value=httpx.Response(200, content=_sse_answer(), headers={"content-type": "text/event-stream"}))

    out = await search_munich_ris("Welche Anträge gibt es zum Radverkehr?")

    assert out.startswith("Es gibt Anträge zum Radverkehr.")
    assert "Quelle: Beschlussvorlage Radwege." in out


async def test_search_blank_question_short_circuits(configured: None) -> None:
    out = await search_munich_ris("   ")
    assert "Bitte stelle eine Frage" in out


@respx.mock
async def test_search_backend_down_is_friendly(configured: None) -> None:
    respx.post(AGENT_URL).mock(side_effect=httpx.ConnectError("down"))

    out = await search_munich_ris("Frage")
    assert "technisches Problem" in out
    assert "Traceback" not in out


async def test_search_unconfigured_returns_clear_message(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RISKI_MCP__BACKEND_URL", raising=False)
    get_settings.cache_clear()
    try:
        out = await search_munich_ris("Frage")
    finally:
        get_settings.cache_clear()
    assert "nicht konfiguriert" in out


async def test_get_riski_capabilities_describes_ris() -> None:
    out = await get_riski_capabilities()
    assert "RIS" in out
    assert "München" in out
