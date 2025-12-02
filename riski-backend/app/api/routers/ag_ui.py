from ag_ui.core.types import RunAgentInput
from ag_ui.encoder import EventEncoder
from app.agent import get_riski_agent
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api/ag-ui", tags=["ag-ui"])
_agent = get_riski_agent()


@router.post("/riskiagent", response_class=StreamingResponse)
async def invoke_riski_agent(input_data: RunAgentInput, request: Request) -> StreamingResponse:
    """Stream LangGraph events back to AG-UI clients."""

    encoder = EventEncoder(accept=request.headers.get("accept"))

    async def event_generator():
        async for event in _agent.run(input_data):
            yield encoder.encode(event)

    return StreamingResponse(event_generator(), media_type=encoder.get_content_type())
