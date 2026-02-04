from unittest.mock import AsyncMock, MagicMock, patch

from app.backend import backend
from fastapi.testclient import TestClient
from langchain_core.documents import Document


def _build_document_candidates(*args, **kwargs) -> list[Document]:
    return [
        Document(page_content="Riski ist ein Informationssystem.", metadata={"source": "doc1", "id": "1"}),
    ]


def test_ag_ui_riskiagent_endpoint_streams_mock_answer() -> None:
    mock_vectorstore = MagicMock()
    mock_vectorstore.similarity_search.side_effect = _build_document_candidates
    mock_engine = MagicMock()
    mock_engine.close = AsyncMock()

    # Create a mock agent that simulates the run method
    mock_agent = AsyncMock()

    async def mock_agent_run(*args, **kwargs):
        mock_event = MagicMock()
        # Mocking ProcessedEvents structure
        mock_event.type = "event"
        mock_event.event = {"event": "on_chat_model_stream", "tags": []}
        mock_event.content = "Riski answer chunk"
        yield mock_event

    # Configure the mock agent's run method to return the async generator
    mock_agent.run.side_effect = mock_agent_run

    with (
        patch("app.backend.build_vectorstore", return_value=(mock_vectorstore, mock_engine)),
        patch("app.backend.build_agent", return_value=mock_agent),
    ):
        with TestClient(backend) as client:
            payload = {
                "threadId": "test-thread",
                "runId": "test-run",
                "state": {},
                "messages": [
                    {
                        "id": "msg-1",
                        "role": "user",
                        "content": "Was ist RISKI?",
                    }
                ],
                "tools": [],
                "context": [],
                "forwardedProps": {},
            }

            response = client.post(
                "/api/ag-ui/riskiagent",
                json=payload,
                headers={"accept": "text/event-stream"},
            )

            assert response.status_code == 200
            assert "text/event-stream" in response.headers["content-type"]

        mock_engine.close.assert_awaited_once()
