from app.backend import backend
from fastapi.testclient import TestClient


def test_ag_ui_riskiagent_endpoint_streams_mock_answer() -> None:
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
