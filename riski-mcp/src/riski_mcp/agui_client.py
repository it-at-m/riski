"""AG-UI SSE stream client and answer aggregation (issue #03).

The core of the wrapper: POST a :class:`~riski_mcp.models.RunAgentInput` to the
backend's ``/api/ag-ui/riskiagent`` endpoint, consume the AG-UI Server-Sent Event
stream, and fold it into a single :class:`RiskiAnswer`.

The event stream is treated as the contract — we deliberately do **not** import
any backend internals. Event shapes are taken from the AG-UI protocol and
``docs/issues/03-ag-ui-stream-client.md``:

* The final answer streams as ``TEXT_MESSAGE_CONTENT`` deltas between a
  ``TEXT_MESSAGE_START`` / ``TEXT_MESSAGE_END`` pair. The server only forwards the
  ``model``-node text emitted after a tool call, so the concatenated deltas are
  the answer. The content is a JSON ``StructuredAgentResponse``; we extract its
  ``response`` field and fall back to the raw text if it isn't valid JSON.
* ``STATE_SNAPSHOT.snapshot`` carries ``tracked_documents``,
  ``tracked_proposals``, ``user_query`` and ``error_info``. We keep the last
  snapshot; ``error_info`` is ``null`` when there is no error.
* ``RUN_ERROR`` signals an internal backend error; ``RUN_FINISHED`` ends the run.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from types import TracebackType
from typing import Any, Self

import httpx

from riski_mcp.models import build_run_input

__all__ = [
    "AguiClient",
    "ErrorInfo",
    "RiskiAnswer",
    "ERROR_TIMEOUT",
    "ERROR_RUN_ERROR",
    "DEFAULT_REQUEST_TIMEOUT_SECONDS",
    "DEFAULT_CONNECT_TIMEOUT_SECONDS",
]

logger = logging.getLogger(__name__)

_AGENT_PATH = "/api/ag-ui/riskiagent"

DEFAULT_REQUEST_TIMEOUT_SECONDS = 60.0
DEFAULT_CONNECT_TIMEOUT_SECONDS = 10.0

#: Synthetic ``error_type`` values the client mints for transport-level failures
#: (the backend only ever sends business error types in ``error_info``).
ERROR_TIMEOUT = "timeout"
ERROR_RUN_ERROR = "run_error"


@dataclass
class ErrorInfo:
    """A backend error surfaced to the caller (mapped to spoken text in #07)."""

    error_type: str
    message: str = ""
    suggestions: list[str] = field(default_factory=list)


@dataclass
class RiskiAnswer:
    """The aggregated result of one agent run.

    ``answer`` is the final human-readable text (empty when an error preempted
    the answer). ``documents`` / ``proposals`` come from the last
    ``STATE_SNAPSHOT``. ``error`` is set when the run failed or returned no
    answer.
    """

    answer: str = ""
    documents: list[dict] = field(default_factory=list)
    proposals: list[dict] = field(default_factory=list)
    error: ErrorInfo | None = None


class AguiClient:
    """Streams a question through the backend's AG-UI agent endpoint.

    Use as an async context manager so the connection pool is closed::

        async with AguiClient("https://backend.example") as client:
            answer = await client.ask("Wann tagt der Stadtrat?")
    """

    def __init__(
        self,
        base_url: str,
        *,
        request_timeout: float = DEFAULT_REQUEST_TIMEOUT_SECONDS,
        connect_timeout: float = DEFAULT_CONNECT_TIMEOUT_SECONDS,
        headers: dict[str, str] | None = None,
        verify: bool = True,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        """Create an AG-UI streaming client.

        Args:
            base_url: Backend root, e.g. ``https://riski.example``.
            request_timeout: Overall wall-clock budget for one run; the stream is
                cancelled cleanly when it is exceeded.
            connect_timeout: httpx connect timeout.
            headers: Extra headers to send (e.g. auth). ``Accept`` is set for you.
            verify: Whether to verify TLS certificates.
            client: Pre-built ``httpx.AsyncClient`` (mainly for tests); when given,
                ``connect_timeout``/``headers``/``verify`` are assumed baked in.
        """
        self._base_url = base_url.rstrip("/")
        self._request_timeout = request_timeout
        merged_headers = {"Accept": "text/event-stream"}
        if headers:
            merged_headers.update(headers)
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(request_timeout, connect=connect_timeout),
            headers=merged_headers,
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

    async def ask(self, question: str) -> RiskiAnswer:
        """Run ``question`` through the agent and aggregate the event stream.

        Never raises for backend/transport problems: timeouts, disconnects,
        ``RUN_ERROR`` and malformed streams all become a :class:`RiskiAnswer`
        with ``error`` set, so the caller can always produce a spoken sentence.

        Args:
            question: The user's RIS question, as plain text.

        Returns:
            The aggregated :class:`RiskiAnswer`.
        """
        payload = build_run_input(question).model_dump()
        try:
            async with asyncio.timeout(self._request_timeout):
                return await self._run(payload)
        except (TimeoutError, httpx.TimeoutException):
            logger.warning("AG-UI run timed out after %.0fs", self._request_timeout)
            return RiskiAnswer(error=ErrorInfo(error_type=ERROR_TIMEOUT))
        except httpx.HTTPError as exc:
            logger.warning("AG-UI run failed: %s", type(exc).__name__)
            return RiskiAnswer(error=ErrorInfo(error_type=ERROR_RUN_ERROR))

    async def _run(self, payload: dict) -> RiskiAnswer:
        aggregator = _StreamAggregator()
        async with self._client.stream("POST", _AGENT_PATH, json=payload) as response:
            response.raise_for_status()
            async for event in _iter_sse_events(response):
                if aggregator.handle(event):
                    break
        return aggregator.finish()


class _StreamAggregator:
    """State machine that folds AG-UI events into a :class:`RiskiAnswer`."""

    def __init__(self) -> None:
        self._current_text: list[str] = []
        self._last_completed_text: str | None = None
        self._snapshot: dict[str, Any] = {}
        self._run_error: ErrorInfo | None = None

    def handle(self, event: dict[str, Any]) -> bool:
        """Process one event. Returns ``True`` when the run is finished."""
        event_type = event.get("type")

        if event_type == "TEXT_MESSAGE_START":
            self._current_text = []
        elif event_type == "TEXT_MESSAGE_CONTENT":
            delta = event.get("delta")
            if isinstance(delta, str):
                self._current_text.append(delta)
        elif event_type == "TEXT_MESSAGE_END":
            if self._current_text:
                self._last_completed_text = "".join(self._current_text)
            self._current_text = []
        elif event_type == "STATE_SNAPSHOT":
            snapshot = event.get("snapshot")
            if isinstance(snapshot, dict):
                self._snapshot = snapshot
        elif event_type == "RUN_ERROR":
            message = event.get("message")
            self._run_error = ErrorInfo(
                error_type=ERROR_RUN_ERROR,
                message=message if isinstance(message, str) else "",
            )
        elif event_type == "RUN_FINISHED":
            return True

        return False

    def finish(self) -> RiskiAnswer:
        # Snapshot docs/proposals are the fallback source. tracked_documents are
        # slim (name only inside ``metadata``); keep relevant ones. tracked_proposals
        # already carry ``name`` + ``subject``.
        snapshot_docs = [d for d in _as_dict_list(self._snapshot.get("tracked_documents")) if d.get("is_relevant", True)]
        snapshot_proposals = _as_dict_list(self._snapshot.get("tracked_proposals"))

        # A backend RUN_ERROR outranks everything else.
        if self._run_error is not None:
            return RiskiAnswer(documents=snapshot_docs, proposals=snapshot_proposals, error=self._run_error)

        error = _parse_error_info(self._snapshot.get("error_info"))
        if error is not None:
            # An error preempts the answer; the caller formats the message.
            return RiskiAnswer(documents=snapshot_docs, proposals=snapshot_proposals, error=error)

        # Prefer a fully completed message; fall back to a dangling buffer if the
        # stream ended without a TEXT_MESSAGE_END.
        raw = self._last_completed_text
        if raw is None and self._current_text:
            raw = "".join(self._current_text)

        answer, struct_docs, struct_proposals = _parse_structured(raw) if raw is not None else ("", [], [])
        # The StructuredAgentResponse carries clean DocumentReference / ProposalReference
        # entries (name, subject, risUrl); prefer them over the slim snapshot.
        return RiskiAnswer(
            answer=answer,
            documents=struct_docs or snapshot_docs,
            proposals=struct_proposals or snapshot_proposals,
        )


def _parse_structured(raw: str) -> tuple[str, list[dict], list[dict]]:
    """Parse the model-node text into ``(answer, documents, proposals)``.

    The text is a JSON ``StructuredAgentResponse``: ``response`` is the spoken
    answer, ``documents`` are ``DocumentReference`` objects (``name``, ``risUrl``,
    …) and ``proposals`` are ``ProposalReference`` objects (``name``, ``subject``,
    …). Degrades gracefully: invalid JSON is returned as the raw answer text; a
    structured object without a usable ``response`` yields an empty answer (so we
    never speak raw JSON) but still surfaces any documents/proposals.
    """
    text = raw.strip()
    if not text:
        return "", [], []
    try:
        parsed = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return text, [], []
    if isinstance(parsed, dict):
        response = parsed.get("response")
        answer = response.strip() if isinstance(response, str) and response.strip() else ""
        return answer, _as_dict_list(parsed.get("documents")), _as_dict_list(parsed.get("proposals"))
    if isinstance(parsed, str) and parsed.strip():
        return parsed.strip(), [], []
    return text, [], []


def _parse_error_info(value: Any) -> ErrorInfo | None:
    """Map a snapshot ``error_info`` object to :class:`ErrorInfo` (``None`` if absent)."""
    if not isinstance(value, dict):
        return None
    error_type = value.get("error_type")
    if not isinstance(error_type, str) or not error_type:
        return None
    message = value.get("message")
    suggestions = value.get("suggestions")
    return ErrorInfo(
        error_type=error_type,
        message=message if isinstance(message, str) else "",
        suggestions=[s for s in suggestions if isinstance(s, str)] if isinstance(suggestions, list) else [],
    )


def _as_dict_list(value: Any) -> list[dict]:
    """Coerce a snapshot field into a list of dicts, dropping anything else."""
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


async def _iter_sse_events(response: httpx.Response):
    """Yield decoded AG-UI events from an SSE response.

    Parses ``event:`` / ``data:`` frames separated by blank lines. ``data`` is
    JSON-decoded; the AG-UI ``type`` lives inside the JSON, but a bare ``event:``
    name is honoured as a fallback. Malformed frames are skipped rather than
    raising, so a single bad frame can't abort the stream.
    """
    data_lines: list[str] = []
    event_name: str | None = None

    async for line in response.aiter_lines():
        if line == "":
            event = _decode_frame(event_name, data_lines)
            if event is not None:
                yield event
            data_lines = []
            event_name = None
            continue
        if line.startswith(":"):
            continue  # SSE comment / keep-alive
        if line.startswith("data:"):
            data_lines.append(line[len("data:") :].lstrip())
        elif line.startswith("event:"):
            event_name = line[len("event:") :].strip()

    # Flush a trailing frame that wasn't terminated by a blank line.
    event = _decode_frame(event_name, data_lines)
    if event is not None:
        yield event


def _decode_frame(event_name: str | None, data_lines: list[str]) -> dict[str, Any] | None:
    if not data_lines:
        return None
    data = "\n".join(data_lines)
    try:
        parsed = json.loads(data)
    except (json.JSONDecodeError, ValueError):
        logger.debug("skipping malformed SSE frame")
        return None
    if not isinstance(parsed, dict):
        return None
    if "type" not in parsed and event_name:
        parsed["type"] = event_name
    return parsed
