from fastapi.testclient import TestClient

from app.main import create_app


def test_health():
    with TestClient(create_app()) as client:
        health = client.get("/api/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"
        assert health.json()["knowledge_documents"] == 9


def test_empty_conversation_endpoints():
    with TestClient(create_app()) as client:
        messages = client.get("/api/conversations/none/messages")
        assert messages.status_code == 200
        assert messages.json() == []

        sidebar = client.get("/api/conversations/none/sidebar")
        assert sidebar.status_code == 200
        assert sidebar.json()["intent"] == "unknown"


def test_knowledge_upload_increases_count():
    with TestClient(create_app()) as client:
        result = client.post(
            "/api/knowledge",
            json={
                "title": "warranty-terms",
                "content": "# Warranty Terms\nKeywords: warranty\n12 months on repairs.",
            },
        )
        assert result.status_code == 200
        assert result.json()["knowledge_documents"] == 10


def test_duplicate_agent_message_is_dropped_and_conversation_labeled():
    with TestClient(create_app()) as client:
        with client.websocket_connect("/ws/dup-1") as ws:
            ws.send_json(
                {
                    "type": "message",
                    "message": {"role": "agent", "content": "Checking claim CLM-1234567 now."},
                }
            )
            ws.receive_json()
            ws.send_json(
                {
                    "type": "message",
                    "message": {"role": "agent", "content": "Checking claim CLM-1234567 now."},
                }
            )
            ws.send_json(
                {"type": "message", "message": {"role": "agent", "content": "Anything else?"}}
            )
            ws.receive_json()

        messages = client.get("/api/conversations/dup-1/messages").json()
        assert [m["content"] for m in messages] == [
            "Checking claim CLM-1234567 now.",
            "Anything else?",
        ]

        listing = client.get("/api/conversations").json()
        entry = next(c for c in listing if c["conversation_id"] == "dup-1")
        assert entry["label"] == "CLM-1234567"


def test_export_contains_messages_with_timestamps_and_metadata():
    with TestClient(create_app()) as client:
        with client.websocket_connect("/ws/exp-1") as ws:
            ws.send_json(
                {
                    "type": "message",
                    "message": {"role": "agent", "content": "Claim CLM-7654321 received."},
                }
            )
            ws.receive_json()

        export = client.get("/api/conversations/exp-1/export")
        assert export.status_code == 200
        assert "attachment" in export.headers["content-disposition"]
        data = export.json()
        assert data["label"] == "CLM-7654321"
        assert data["message_count"] == 1
        assert data["messages"][0]["ts"] is not None
        assert data["tokens_used"] == {"input": 0, "output": 0, "total": 0}
        assert data["model"]


def test_delete_conversation_removes_state_and_listing():
    with TestClient(create_app()) as client:
        with client.websocket_connect("/ws/gone-1") as ws:
            ws.send_json({"type": "message", "message": {"role": "agent", "content": "note"}})
            ws.receive_json()

        assert client.delete("/api/conversations/gone-1").status_code == 200
        assert "gone-1" not in [
            c["conversation_id"] for c in client.get("/api/conversations").json()
        ]
        assert client.get("/api/conversations/gone-1/messages").json() == []
