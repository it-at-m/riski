from typing import Any, AsyncGenerator

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


@router.post("/riskiagent", response_class=StreamingResponse)
async def invoke_riski_agent(input_data: RunAgentInput, request: Request) -> StreamingResponse:
    """Stream LangGraph events back to AG-UI clients."""

    encoder = EventEncoder(accept=request.headers.get("accept", ""))

    async def event_generator() -> AsyncGenerator[bytes, None]:
        async for event in run_agent_traced(input_data, request):
            raw_event = getattr(event, "event", None)
            event_name = raw_event.get("event") if isinstance(raw_event, dict) else None
            tags = raw_event.get("tags") if isinstance(raw_event, dict) else None
            logger.debug("type=%s event=%s tags=%s", event.type, event_name, tags)
            yield encoder.encode(event)

    return StreamingResponse(event_generator(), media_type=encoder.get_content_type())
