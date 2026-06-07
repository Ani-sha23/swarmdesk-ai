"""API endpoint tests using FastAPI TestClient."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from api.main import app

client_test = TestClient(app)


def make_mock_result(escalated=False, confidence=88):
    return {
        "ticket_id": "mock-ticket-001",
        "user_id": "user_001",
        "response": None if escalated else "Here is your answer.",
        "escalated": escalated,
        "escalation_bundle": None,
        "confidence": confidence,
        "verdict": "FAIL" if escalated else "PASS",
        "task_graph": {"sub_tasks": [], "priority": "normal", "needs_human_flag": False, "summary": ""},
        "agent_traces": [
            {"agent": "PlannerAgent", "action": "decompose_ticket", "output": "2 sub-tasks", "duration_ms": 100},
            {"agent": "RetrieverAgent", "action": "semantic_search", "output": "2 docs", "duration_ms": 50},
            {"agent": "ResponderAgent", "action": "draft_response", "output": "draft ready", "duration_ms": 200},
            {"agent": "ValidatorAgent", "action": "score_response", "output": f"Score: {confidence}/100", "duration_ms": 150},
        ],
        "total_duration_ms": 500,
    }


def test_health_check():
    resp = client_test.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "SwarmDesk AI"


@patch("api.routes.tickets.run_swarm", return_value=make_mock_result())
def test_submit_ticket_success(mock_swarm):
    resp = client_test.post("/api/tickets", json={
        "user_id": "user_001",
        "subject": "Billing issue",
        "body": "I was charged twice for my subscription.",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["ticket_id"] == "mock-ticket-001"
    assert data["escalated"] is False
    assert data["response"] == "Here is your answer."
    assert data["confidence"] == 88
    assert len(data["agent_traces"]) == 4


@patch("api.routes.tickets.run_swarm", return_value=make_mock_result(escalated=True, confidence=40))
def test_submit_ticket_escalated(mock_swarm):
    resp = client_test.post("/api/tickets", json={
        "user_id": "user_002",
        "subject": "Account hacked",
        "body": "Someone hacked my account and changed my payment method.",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["escalated"] is True
    assert data["response"] is None
    assert data["confidence"] == 40


def test_submit_ticket_missing_body():
    resp = client_test.post("/api/tickets", json={"user_id": "u1", "subject": "Test"})
    assert resp.status_code == 422


def test_submit_ticket_invalid_priority():
    resp = client_test.post("/api/tickets", json={
        "user_id": "u1", "subject": "Test", "body": "Test body", "priority": "extreme"
    })
    assert resp.status_code == 422
