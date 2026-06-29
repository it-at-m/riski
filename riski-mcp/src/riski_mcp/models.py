"""Typed wire models for the RISKI backend (issue #02).

These model the *subset* of the backend contract the MCP wrapper needs, derived
from ``riski-backend/openapi.json``. We hand-write them (only a handful are
needed) rather than running ``datamodel-code-generator`` over the full spec: the
backend exposes a large multimodal message union we never produce, and a thin
hand-written subset keeps the wrapper decoupled from backend internals.

If the backend bumps its OpenAPI version, re-verify these against
``openapi.json`` — see ``test/test_models.py::test_run_input_matches_openapi``.
"""

from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, Field

__all__ = [
    "UserMessage",
    "RunAgentInput",
    "ConfigResponse",
    "HealthCheckResponse",
    "build_run_input",
]


class UserMessage(BaseModel):
    """A user message — the only message kind the wrapper produces.

    The backend's ``content`` accepts multimodal arrays, but for a spoken RIS
    question we only ever send plain text.
    """

    id: str
    role: Literal["user"] = "user"
    content: str


class RunAgentInput(BaseModel):
    """Request body for ``POST /api/ag-ui/riskiagent``.

    Required by the backend: ``threadId``, ``runId``, ``state``, ``messages``,
    ``tools``, ``context``, ``forwardedProps``. The wrapper is stateless, so we
    send empty defaults for everything except the messages.
    """

    threadId: str
    runId: str
    state: dict = Field(default_factory=dict)
    messages: list[UserMessage] = Field(default_factory=list)
    tools: list[dict] = Field(default_factory=list)
    context: list[dict] = Field(default_factory=list)
    forwardedProps: dict = Field(default_factory=dict)


class ConfigResponse(BaseModel):
    """Response of ``GET /api/config``."""

    version: str
    frontend_version: str
    title: str
    documentation_url: str
    contact_url: str
    impressum_url: str
    townhallbulletin_url: str


class HealthCheckResponse(BaseModel):
    """Response of ``GET /api/healthz``."""

    status: str = "ok"
    version: str


def build_run_input(question: str) -> RunAgentInput:
    """Build a stateless ``RunAgentInput`` for a single spoken question.

    Mints fresh ``threadId``/``runId``/message-``id`` (uuid4) on every call so
    each MCP tool invocation is an independent run, per the stateless-tool
    requirement.

    Args:
        question: The user's RIS question, as plain text.

    Returns:
        A fully-populated ``RunAgentInput`` ready to POST to the agent endpoint.
    """
    return RunAgentInput(
        threadId=str(uuid.uuid4()),
        runId=str(uuid.uuid4()),
        messages=[UserMessage(id=str(uuid.uuid4()), content=question)],
    )
