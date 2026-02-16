from typing import Any, AsyncGenerator

from ag_ui.core import RunErrorEvent
from ag_ui.core.types import RunAgentInput
from ag_ui.encoder import EventEncoder
from ag_ui_langgraph.agent import ProcessedEvents
from app.agent.state import ErrorInfo, RelevanceUpdate, TrackedDocument, TrackedProposal
from app.utils.logging import getLogger
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from langfuse import observe

router = APIRouter(prefix="/api/ag-ui", tags=["ag-ui"])
logger = getLogger()


@observe(name="ag-ui-agent-run")
async def run_agent_traced(input_data: RunAgentInput, request: Request) -> AsyncGenerator[ProcessedEvents, None]:
    async for event in request.app.state.agent.run(input_data):
        yield event


def encode(encoder, event):
    raw_event = getattr(event, "event", None)
    event_name = raw_event.get("event") if isinstance(raw_event, dict) else None
    tags = raw_event.get("tags") if isinstance(raw_event, dict) else None
    logger.debug("type=%s event=%s tags=%s", event.type, event_name, tags)
    return encoder.encode(event)


class SnapshotStripper:
    """Stateful snapshot processor that caches ``tracked_documents``.

    ag-ui-langgraph builds its intermediate ``STATE_SNAPSHOT`` by calling
    ``current_graph_state.update(node_output)`` which **replaces**
    ``tracked_documents`` with the raw node return value.  For
    ``check_document`` nodes that means a single ``RelevanceUpdate``
    instead of the full list.

    This class keeps a running copy of the last-known full document list
    and merges any ``RelevanceUpdate`` entries into it – mirroring the
    same logic the LangGraph reducer uses.
    """

    def __init__(self) -> None:
        self._cached_docs: list[TrackedDocument] = []

    def strip(self, event: ProcessedEvents) -> ProcessedEvents:
        """Reduce STATE_SNAPSHOT payload to a lightweight summary."""
        if getattr(event, "type", None) != "STATE_SNAPSHOT":
            return event

        # Drop raw_event entirely to avoid duplicating payloads
        event.raw_event = None

        snapshot: dict[str, Any] | None = getattr(event, "snapshot", None)
        if not isinstance(snapshot, dict):
            return event

        # -- Slim messages (same as before) --
        messages = snapshot.get("messages")
        slim_messages: list[dict[str, Any]] = []
        if isinstance(messages, list):
            for msg in messages:
                if not isinstance(msg, dict):
                    continue
                slim_msg: dict[str, Any] = {
                    "id": msg.get("id") or msg.get("message_id"),
                    "type": msg.get("type"),
                }
                tool_calls = msg.get("tool_calls")
                if isinstance(tool_calls, list):
                    slim_calls: list[dict[str, Any]] = []
                    for call in tool_calls:
                        if isinstance(call, dict):
                            slim_calls.append(
                                {
                                    "id": call.get("id"),
                                    "name": call.get("name"),
                                    "type": call.get("type"),
                                }
                            )
                    if slim_calls:
                        slim_msg["tool_calls"] = slim_calls
                slim_messages.append(slim_msg)

        # -- Merge tracked_documents with cached state -------------------------
        raw_docs: list[TrackedDocument | RelevanceUpdate] = snapshot.get("tracked_documents", [])
        self._merge_docs(raw_docs)
        slim_docs: list[dict[str, Any]] = [doc.to_slim_dict() for doc in self._cached_docs]

        # -- tracked_proposals pass through as model_dump() (already lightweight)
        tracked_proposals: list[TrackedProposal] = snapshot.get("tracked_proposals", [])

        # -- error_info pass through (None when no error)
        error_info_raw = snapshot.get("error_info")
        error_info_dict: dict[str, Any] | None = None
        if isinstance(error_info_raw, ErrorInfo):
            error_info_dict = error_info_raw.model_dump()
        elif isinstance(error_info_raw, dict):
            error_info_dict = error_info_raw

        event.snapshot = {
            "messages": slim_messages,
            "tracked_documents": slim_docs,
            "tracked_proposals": [p.model_dump() for p in tracked_proposals],
            "user_query": snapshot.get("user_query", ""),
            "error_info": error_info_dict,
        }
        return event

    # ------------------------------------------------------------------

    def _merge_docs(self, raw: list[TrackedDocument | RelevanceUpdate]) -> None:
        """Update the internal document cache.

        - If the list contains ``TrackedDocument`` entries, replace the cache.
        - If it contains ``RelevanceUpdate`` entries, patch the cached docs.
        - Mixed / empty lists are handled gracefully.
        """
        if not raw:
            return

        updates: list[RelevanceUpdate] = [d for d in raw if isinstance(d, RelevanceUpdate)]
        full_docs: list[TrackedDocument] = [d for d in raw if isinstance(d, TrackedDocument)]

        if full_docs:
            # Full replacement (e.g. from the tool node or final snapshot)
            self._cached_docs = full_docs

        if updates:
            # Incremental patch – merge relevance results into cached docs
            by_id: dict[str, RelevanceUpdate] = {u.doc_id: u for u in updates}
            patched: list[TrackedDocument] = []
            for doc in self._cached_docs:
                if doc.id in by_id:
                    upd = by_id[doc.id]
                    doc = doc.model_copy(
                        update={
                            "is_checked": True,
                            "is_relevant": upd.is_relevant,
                            "relevance_reason": upd.reason,
                        }
                    )
                patched.append(doc)
            self._cached_docs = patched


def _is_check_document_node(event: Any) -> bool:
    """Return True for non-snapshot events from check_document nodes.

    We want to suppress ``STEP_STARTED`` / ``STEP_FINISHED`` for
    ``check_document`` (they create UI noise) but we must **not** suppress
    ``STATE_SNAPSHOT`` events – the ``SnapshotStripper`` needs them to
    accumulate each ``RelevanceUpdate`` incrementally.
    """
    if getattr(event, "type", None) == "STATE_SNAPSHOT":
        return False

    raw_event = getattr(event, "raw_event", None)
    if not isinstance(raw_event, dict):
        return False

    metadata = raw_event.get("metadata")
    return isinstance(metadata, dict) and metadata.get("langgraph_node") == "check_document"


@router.post("/riskiagent", response_class=StreamingResponse)
async def invoke_riski_agent(input_data: RunAgentInput, request: Request) -> StreamingResponse:
    """Stream LangGraph events back to AG-UI clients."""

    encoder = EventEncoder(accept=request.headers.get("accept", ""))
    allowed_types = {
        "RUN_STARTED",
        "RUN_FINISHED",
        "STEP_STARTED",
        "STEP_FINISHED",
        "STATE_SNAPSHOT",
        "TEXT_MESSAGE_CONTENT",
        "TEXT_MESSAGE_START",
        "TEXT_MESSAGE_END",
        "RUN_ERROR",
    }
    text_message_types = {"TEXT_MESSAGE_CONTENT", "TEXT_MESSAGE_START", "TEXT_MESSAGE_END"}

    snapshot_stripper = SnapshotStripper()

    async def event_generator() -> AsyncGenerator[bytes, None]:
        try:
            async for event in run_agent_traced(input_data, request):
                if _is_check_document_node(event):
                    continue
                if event.type in allowed_types:
                    if event.type == "STATE_SNAPSHOT":
                        event = snapshot_stripper.strip(event)
                    if event.type in text_message_types:
                        event.raw_event = None
                    yield encode(encoder=encoder, event=event)
                else:
                    logger.info("Unrecognized event type: %s", event.type)
        except Exception as e:
            logger.error("Error in agent run: %s", e, exc_info=True)
            yield encode(encoder=encoder, event=RunErrorEvent(message="Ein interner Fehler ist aufgetreten."))

    return StreamingResponse(event_generator(), media_type=encoder.get_content_type())
