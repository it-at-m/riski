from ag_ui.core.types import RunAgentInput
from ag_ui.encoder import EventEncoder
from app.utils.logging import getLogger
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from langfuse import observe

router = APIRouter(prefix="/api/ag-ui", tags=["ag-ui"])
logger = getLogger()


@observe(name="ag-ui-agent-run")
async def run_agent_traced(input_data, request):
    async for event in request.app.state.agent.run(input_data):
        yield event


@router.post("/riskiagent", response_class=StreamingResponse)
async def invoke_riski_agent(input_data: RunAgentInput, request: Request) -> StreamingResponse:
    """Stream LangGraph events back to AG-UI clients."""

    encoder = EventEncoder(accept=request.headers.get("accept"))

    async def event_generator():
        async for event in run_agent_traced(input_data, request):
            event_type = getattr(event, "type", None)
            ev = getattr(event, "event", None)
            if isinstance(ev, dict):
                event_val = ev.get("event")
                tags_val = ev.get("tags")
            else:
                event_val = getattr(ev, "event", None) if ev is not None else None
                tags_val = getattr(ev, "tags", None) if ev is not None else None
            logger.debug("type=%s event=%s tags=%s", event_type, event_val, tags_val)
            yield encoder.encode(event)

    return StreamingResponse(event_generator(), media_type=encoder.get_content_type())
