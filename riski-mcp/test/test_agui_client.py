"""Tests for the AG-UI SSE stream client and aggregation (issue #03)."""

from __future__ import annotations

import json

import httpx
import pytest
import respx
from riski_mcp.agui_client import ERROR_RUN_ERROR, ERROR_TIMEOUT, AguiClient

BASE_URL = "https://backend.test"
AGENT_URL = f"{BASE_URL}/api/ag-ui/riskiagent"


def _sse(events: list[dict]) -> bytes:
    """Encode events as an AG-UI SSE stream (``data: <json>`` frames)."""
    return "".join(f"data: {json.dumps(e)}\n\n" for e in events).encode("utf-8")


def _structured(response: str, documents: list[dict] | None = None, proposals: list[dict] | None = None) -> str:
    return json.dumps(
        {
            "response": response,
            "documents": documents or [],
            "proposals": proposals or [],
        }
    )


def _text_message(payload: str, *, chunks: int = 1, message_id: str = "m1") -> list[dict]:
    """Build START / CONTENT* / END events carrying ``payload`` (optionally split)."""
    size = max(1, len(payload) // chunks)
    pieces = [payload[i : i + size] for i in range(0, len(payload), size)] or [""]
    events: list[dict] = [{"type": "TEXT_MESSAGE_START", "messageId": message_id}]
    events += [{"type": "TEXT_MESSAGE_CONTENT", "messageId": message_id, "delta": p} for p in pieces]
    events.append({"type": "TEXT_MESSAGE_END", "messageId": message_id})
    return events


def _mock_stream(content: bytes) -> None:
    respx.post(AGENT_URL).mock(return_value=httpx.Response(200, content=content, headers={"content-type": "text/event-stream"}))


@respx.mock
async def test_happy_path_answer_documents_proposals() -> None:
    payload = _structured(
        "Es gibt mehrere Anträge zum Radverkehr in München.",
        documents=[{"name": "Beschlussvorlage Radwege", "risUrl": "https://ris/doc/1"}],
        proposals=[{"identifier": "p1", "name": "Antrag Radverkehr", "subject": "Ausbau der Radwege"}],
    )
    events = [
        {"type": "RUN_STARTED", "threadId": "t", "runId": "r"},
        {"type": "TOOL_CALL_START", "toolCallId": "c1"},
        {"type": "TOOL_CALL_END", "toolCallId": "c1"},
        {
            "type": "STATE_SNAPSHOT",
            "snapshot": {
                "tracked_documents": [{"id": "d1", "metadata": {"name": "raw"}, "is_relevant": True}],
                "tracked_proposals": [{"identifier": "p1", "name": "Antrag Radverkehr", "subject": "Ausbau der Radwege"}],
                "user_query": "Radverkehr?",
                "error_info": None,
            },
        },
        *_text_message(payload, chunks=3),
        {"type": "RUN_FINISHED", "threadId": "t", "runId": "r"},
    ]
    _mock_stream(_sse(events))

    async with AguiClient(BASE_URL) as client:
        answer = await client.ask("Radverkehr?")

    assert answer.error is None
    assert answer.answer == "Es gibt mehrere Anträge zum Radverkehr in München."
    # Documents/proposals come from the structured response (clean names), not the slim snapshot.
    assert answer.documents == [{"name": "Beschlussvorlage Radwege", "risUrl": "https://ris/doc/1"}]
    assert answer.proposals[0]["subject"] == "Ausbau der Radwege"


@respx.mock
async def test_accept_header_sent() -> None:
    _mock_stream(_sse([{"type": "RUN_FINISHED"}]))

    async with AguiClient(BASE_URL) as client:
        await client.ask("hi")

    assert respx.calls.last.request.headers["accept"] == "text/event-stream"


@respx.mock
async def test_no_documents_found_sets_error_and_empty_answer() -> None:
    events = [
        {
            "type": "STATE_SNAPSHOT",
            "snapshot": {
                "tracked_documents": [],
                "tracked_proposals": [],
                "error_info": {
                    "error_type": "no_documents_found",
                    "message": "Keine Dokumente gefunden.",
                    "suggestions": ["Radverkehr Innenstadt"],
                },
            },
        },
        {"type": "RUN_FINISHED"},
    ]
    _mock_stream(_sse(events))

    async with AguiClient(BASE_URL) as client:
        answer = await client.ask("xyz")

    assert answer.answer == ""
    assert answer.error is not None
    assert answer.error.error_type == "no_documents_found"
    assert answer.error.suggestions == ["Radverkehr Innenstadt"]


@respx.mock
async def test_no_relevant_documents_error() -> None:
    events = [
        {"type": "STATE_SNAPSHOT", "snapshot": {"error_info": {"error_type": "no_relevant_documents", "message": "m"}}},
        {"type": "RUN_FINISHED"},
    ]
    _mock_stream(_sse(events))

    async with AguiClient(BASE_URL) as client:
        answer = await client.ask("q")

    assert answer.error is not None
    assert answer.error.error_type == "no_relevant_documents"


@respx.mock
async def test_run_error_event_maps_to_generic_error() -> None:
    events = [
        {"type": "TEXT_MESSAGE_START", "messageId": "m1"},
        {"type": "TEXT_MESSAGE_CONTENT", "messageId": "m1", "delta": "partial"},
        {"type": "RUN_ERROR", "message": "Ein interner Fehler ist aufgetreten."},
    ]
    _mock_stream(_sse(events))

    async with AguiClient(BASE_URL) as client:
        answer = await client.ask("q")

    assert answer.answer == ""  # RUN_ERROR preempts any partial text
    assert answer.error is not None
    assert answer.error.error_type == ERROR_RUN_ERROR


@respx.mock
async def test_timeout_maps_to_timeout_error() -> None:
    respx.post(AGENT_URL).mock(side_effect=httpx.ReadTimeout("too slow"))

    async with AguiClient(BASE_URL) as client:
        answer = await client.ask("q")

    assert answer.error is not None
    assert answer.error.error_type == ERROR_TIMEOUT


@respx.mock
async def test_connect_error_maps_to_run_error() -> None:
    respx.post(AGENT_URL).mock(side_effect=httpx.ConnectError("down"))

    async with AguiClient(BASE_URL) as client:
        answer = await client.ask("q")

    assert answer.error is not None
    assert answer.error.error_type == ERROR_RUN_ERROR


@respx.mock
async def test_non_2xx_maps_to_run_error() -> None:
    respx.post(AGENT_URL).mock(return_value=httpx.Response(503))

    async with AguiClient(BASE_URL) as client:
        answer = await client.ask("q")

    assert answer.error is not None
    assert answer.error.error_type == ERROR_RUN_ERROR


@respx.mock
async def test_malformed_frame_is_skipped() -> None:
    content = (
        b"data: {not valid json}\n\n"
        + _sse(_text_message(_structured("Antwort trotz Mull.")))
        + b"data: {\n\n"
        + _sse([{"type": "RUN_FINISHED"}])
    )
    _mock_stream(content)

    async with AguiClient(BASE_URL) as client:
        answer = await client.ask("q")

    assert answer.error is None
    assert answer.answer == "Antwort trotz Mull."


@respx.mock
async def test_truncated_stream_without_run_finished() -> None:
    # No RUN_FINISHED and no TEXT_MESSAGE_END: the dangling buffer is still used.
    events = [
        {"type": "TEXT_MESSAGE_START", "messageId": "m1"},
        {"type": "TEXT_MESSAGE_CONTENT", "messageId": "m1", "delta": _structured("Teilantwort.")},
    ]
    _mock_stream(_sse(events))

    async with AguiClient(BASE_URL) as client:
        answer = await client.ask("q")

    assert answer.error is None
    assert answer.answer == "Teilantwort."


@respx.mock
async def test_empty_stream_returns_empty_answer() -> None:
    _mock_stream(b"")

    async with AguiClient(BASE_URL) as client:
        answer = await client.ask("q")

    assert answer.answer == ""
    assert answer.error is None
    assert answer.documents == []


@respx.mock
async def test_plain_text_answer_not_json() -> None:
    # If the model node ever emits non-JSON text, surface it verbatim.
    _mock_stream(_sse([*_text_message("Einfacher Text ohne JSON."), {"type": "RUN_FINISHED"}]))

    async with AguiClient(BASE_URL) as client:
        answer = await client.ask("q")

    assert answer.answer == "Einfacher Text ohne JSON."


@respx.mock
async def test_auth_header_forwarded() -> None:
    _mock_stream(_sse([{"type": "RUN_FINISHED"}]))

    async with AguiClient(BASE_URL, headers={"Authorization": "Bearer secret"}) as client:
        await client.ask("q")

    assert respx.calls.last.request.headers["authorization"] == "Bearer secret"


@pytest.mark.parametrize("base", [BASE_URL, f"{BASE_URL}/"])
@respx.mock
async def test_trailing_slash_normalized(base: str) -> None:
    _mock_stream(_sse([{"type": "RUN_FINISHED"}]))

    async with AguiClient(base) as client:
        answer = await client.ask("q")

    assert answer.error is None
    assert respx.calls.last.request.url == AGENT_URL
