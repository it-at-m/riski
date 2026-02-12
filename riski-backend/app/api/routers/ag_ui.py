import ast
import copy
import re
from typing import Any, AsyncGenerator

from ag_ui.core import RunErrorEvent
from ag_ui.core.types import RunAgentInput
from ag_ui.encoder import EventEncoder
from ag_ui_langgraph.agent import ProcessedEvents
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


def _build_tool_output_summary(output: Any) -> dict[str, Any] | None:
    """Build a lightweight summary from the serialised ToolMessage output.

    After ``make_json_safe`` the tool output is a ToolMessage dict::

        {"content": "<python repr string>",
         "type": "tool", "name": "retrieve_documents", ...}

    ``content`` is a Python repr of ``RetrieveDocumentsOutput`` – a huge
    string that includes every document's ``page_content``.  We cannot
    round-trip it as JSON, so instead we **drop** the content entirely and
    attach a small ``_summary`` key with just the metadata we need.

    To build the summary we look at the *original* ``content`` repr and
    pull out the structured bits with ``ast.literal_eval`` on the proposals
    list (which is plain dicts) while extracting document metadata via
    simple string inspection.
    """
    if not isinstance(output, dict):
        return None

    content = output.get("content")
    if not isinstance(content, str):
        return None

    # Fast path: nothing interesting
    if "documents" not in content and "proposals" not in content:
        return None

    summary: dict[str, Any] = {}

    # --- proposals: plain dicts, easy to extract ---
    proposals_match = re.search(r"'proposals':\s*(\[.*\])", content)
    if proposals_match:
        try:
            summary["proposals"] = ast.literal_eval(proposals_match.group(1))
        except Exception:
            pass

    # --- documents: extract metadata dicts from Document(...) reprs ---
    doc_list: list[dict[str, Any]] = []
    for m in re.finditer(r"Document\(\s*id='([^']*)'\s*,\s*metadata=(\{[^}]*\})", content):
        doc_id = m.group(1)
        try:
            metadata = ast.literal_eval(m.group(2))
        except Exception:
            metadata = {}
        doc_list.append({"id": doc_id, "metadata": metadata})
    if doc_list:
        summary["documents"] = doc_list

    if not summary:
        return None

    return summary


def strip_tool_end_payload(event):
    """Replace the huge ToolMessage content with a lightweight summary."""
    raw = getattr(event, "event", None)
    if not isinstance(raw, dict) or raw.get("event") != "on_tool_end":
        return event

    raw = copy.deepcopy(raw)
    data = raw.get("data", {})
    output = data.get("output")

    summary = _build_tool_output_summary(output)
    if summary is not None:
        # Replace the ToolMessage with just the summary dict
        data["output"] = summary
    elif isinstance(output, dict) and "content" in output:
        # No summary possible – still strip the huge content
        del output["content"]

    event.event = raw
    return event


@router.post("/riskiagent", response_class=StreamingResponse)
async def invoke_riski_agent(input_data: RunAgentInput, request: Request) -> StreamingResponse:
    """Stream LangGraph events back to AG-UI clients."""

    encoder = EventEncoder(accept=request.headers.get("accept", ""))
    allowed_types = {
        "RUN_STARTED",
        "RUN_FINISHED",
        "STEP_STARTED",
        "STEP_FINISHED",
        "TEXT_MESSAGE_CONTENT",
        "TEXT_MESSAGE_START",
        "TEXT_MESSAGE_END",
        "RUN_ERROR",
    }
    text_message_types = {"TEXT_MESSAGE_CONTENT", "TEXT_MESSAGE_START", "TEXT_MESSAGE_END"}
    allowed_raw_events = {"on_tool_start", "on_tool_end"}

    async def event_generator() -> AsyncGenerator[bytes, None]:
        try:
            async for event in run_agent_traced(input_data, request):
                if event.type in allowed_types:
                    if event.type in text_message_types:
                        event.raw_event = None
                    yield encode(encoder=encoder, event=event)
                elif event.type == "RAW":
                    raw_inner = getattr(event, "event", {})
                    if isinstance(raw_inner, dict) and raw_inner.get("event") in allowed_raw_events:
                        event = strip_tool_end_payload(event)
                        yield encode(encoder=encoder, event=event)
                    else:
                        logger.info("Unrecognized RAW event: %s", raw_inner.get("event") if isinstance(raw_inner, dict) else raw_inner)
                else:
                    logger.info("Unrecognized event type: %s", event.type)
        except Exception as e:
            logger.error("Error in agent run: %s", e, exc_info=True)
            yield encode(encoder=encoder, event=RunErrorEvent(message="Ein interner Fehler ist aufgetreten."))

    return StreamingResponse(event_generator(), media_type=encoder.get_content_type())
