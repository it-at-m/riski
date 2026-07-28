"""MCP / Gradio app smoke tests (issue #06, #10)."""

from __future__ import annotations

import os
from collections.abc import Iterator

import httpx
import pytest
from riski_mcp.config import get_settings

BASE_URL = "https://backend.test"


@pytest.fixture
def configured(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("RISKI_MCP__BACKEND_URL", BASE_URL)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_build_demo_when_configured(configured: None) -> None:
    import gradio as gr
    from app import build_demo

    demo = build_demo()
    assert isinstance(demo, gr.Blocks)


def test_build_demo_when_unconfigured(monkeypatch: pytest.MonkeyPatch) -> None:
    # A missing backend URL must not crash the landing page.
    monkeypatch.delenv("RISKI_MCP__BACKEND_URL", raising=False)
    get_settings.cache_clear()
    try:
        import gradio as gr
        from app import build_demo

        demo = build_demo()
        assert isinstance(demo, gr.Blocks)
    finally:
        get_settings.cache_clear()


@pytest.mark.skipif(not os.getenv("RUN_MCP_SMOKE"), reason="set RUN_MCP_SMOKE=1 to run the live MCP launch smoke test")
def test_mcp_endpoint_lists_tools(configured: None) -> None:
    """Launch the app and confirm the MCP endpoint advertises our tools.

    Opt-in (binds a local port) — gated behind RUN_MCP_SMOKE so CI stays fast.
    """
    from app import build_demo

    demo = build_demo()
    demo.launch(server_name="127.0.0.1", mcp_server=True, prevent_thread_lock=True)
    try:
        port = demo.server_port
        resp = httpx.post(
            f"http://127.0.0.1:{port}/gradio_api/mcp/",
            headers={"Accept": "application/json, text/event-stream"},
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
            timeout=10.0,
        )
        body = resp.text
        # The response may be SSE-framed; a substring check keeps this robust.
        assert "search_munich_ris" in body
        assert "get_riski_capabilities" in body
    finally:
        demo.close()
