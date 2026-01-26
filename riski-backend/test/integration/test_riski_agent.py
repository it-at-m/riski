from unittest.mock import AsyncMock, MagicMock, patch

from app.agent.riski_agent import _build_document_candidates
from app.backend import backend
from fastapi.testclient import TestClient


def test_ag_ui_riskiagent_endpoint_streams_mock_answer() -> None:
    mock_vectorstore = MagicMock()
    mock_vectorstore.similarity_search.side_effect = _build_document_candidates
    mock_engine = MagicMock()
    mock_engine.close = AsyncMock()
    with patch("app.backend.get_vectorstore", return_value=(mock_vectorstore, mock_engine)):
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
