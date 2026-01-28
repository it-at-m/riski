from ag_ui.core.types import RunAgentInput
from ag_ui.encoder import EventEncoder
from app.agent import get_riski_agent
from app.utils.logging import getLogger
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from langfuse import observe

router = APIRouter(prefix="/api/ag-ui", tags=["ag-ui"])
logger = getLogger()


@observe(name="ag-ui-agent-run")
async def run_agent_traced(input_data, request):
    _agent = get_riski_agent(request.app.state.vectorstore)
    async for event in _agent.run(input_data):
        yield event


@router.post("/riskiagent", response_class=StreamingResponse)
async def invoke_riski_agent(input_data: RunAgentInput, request: Request) -> StreamingResponse:
    """Stream LangGraph events back to AG-UI clients."""

    encoder = EventEncoder(accept=request.headers.get("accept"))

    async def event_generator():
        async for event in run_agent_traced(input_data, request):
            logger.debug(event)
            yield encoder.encode(event)

    return StreamingResponse(event_generator(), media_type=encoder.get_content_type())
