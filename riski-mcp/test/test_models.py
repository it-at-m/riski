"""Tests for the typed wire models and build_run_input (issue #02)."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest
from riski_mcp.models import RunAgentInput, UserMessage, build_run_input

# riski-mcp/test/test_models.py -> repo root is parents[2]
_OPENAPI_PATH = Path(__file__).resolve().parents[2] / "riski-backend" / "openapi.json"


def test_build_run_input_shape() -> None:
    run = build_run_input("Wann tagt der Stadtrat?")

    assert isinstance(run, RunAgentInput)
    assert len(run.messages) == 1
    msg = run.messages[0]
    assert isinstance(msg, UserMessage)
    assert msg.role == "user"
    assert msg.content == "Wann tagt der Stadtrat?"
    # Stateless defaults.
    assert run.state == {}
    assert run.tools == []
    assert run.context == []
    assert run.forwardedProps == {}


def test_build_run_input_fresh_ids() -> None:
    a = build_run_input("q1")
    b = build_run_input("q2")

    # Fresh, valid uuid4s on every call; nothing shared between runs.
    for run in (a, b):
        uuid.UUID(run.threadId)
        uuid.UUID(run.runId)
        uuid.UUID(run.messages[0].id)
        assert run.threadId != run.runId != run.messages[0].id

    assert a.threadId != b.threadId
    assert a.runId != b.runId
    assert a.messages[0].id != b.messages[0].id


@pytest.mark.skipif(not _OPENAPI_PATH.exists(), reason="backend openapi.json not available")
def test_run_input_matches_openapi() -> None:
    """The payload we produce satisfies the backend's RunAgentInput contract.

    A structural check against ``openapi.json``: every required field of
    ``RunAgentInput`` (and of ``UserMessage``) is present in our serialized
    payload, and the message ``role`` matches the discriminator mapping.
    """
    schemas = json.loads(_OPENAPI_PATH.read_text(encoding="utf-8"))["components"]["schemas"]

    payload = build_run_input("hello").model_dump()

    required = schemas["RunAgentInput"]["required"]
    assert set(required) <= set(payload), f"missing required RunAgentInput fields: {set(required) - set(payload)}"

    user_required = schemas["UserMessage"]["required"]
    message = payload["messages"][0]
    assert set(user_required) <= set(message)

    # role "user" must map to UserMessage in the discriminator.
    mapping = schemas["RunAgentInput"]["properties"]["messages"]["items"]["discriminator"]["mapping"]
    assert mapping[message["role"]].endswith("/UserMessage")
