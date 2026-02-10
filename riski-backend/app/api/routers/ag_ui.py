import copy
from typing import AsyncGenerator

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


def strip_tool_end_payload(event):
    """Remove large data (page_content, full output) from on_tool_end RAW events."""
    raw = getattr(event, "event", None)
    if not isinstance(raw, dict) or raw.get("event") != "on_tool_end":
        return event

    raw = copy.deepcopy(raw)
    data = raw.get("data", {})

    # Remove the large output content (contains full document text)
    if "output" in data:
        del data["output"]

    # Keep only the input query for reference
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
            yield encode(encoder=encoder, event=RunErrorEvent(message=str(e)))

    return StreamingResponse(event_generator(), media_type=encoder.get_content_type())
