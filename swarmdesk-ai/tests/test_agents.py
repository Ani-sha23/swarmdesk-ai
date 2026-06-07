"""
Unit tests for SwarmDesk AI agents.
Run: pytest tests/ -v
"""
import pytest, json, os
from unittest.mock import patch, MagicMock

# ── Fixtures ─────────────────────────────────────────────────────────────────
SAMPLE_TICKET_NORMAL = {
    "subject": "Double charge and dashboard broken",
    "body": (
        "Hi, I was charged twice for my Pro subscription last month. "
        "My dashboard also shows 'subscription inactive'. "
        "I need a refund and access restored."
    ),
}

SAMPLE_TICKET_CRITICAL = {
    "subject": "Account hacked",
    "body": "I think my account was hacked. Someone changed my payment method without my authorization.",
}

SAMPLE_TASK_GRAPH = {
    "sub_tasks": [
        {"id": "t1", "description": "Process double charge refund", "domain": "billing"},
        {"id": "t2", "description": "Restore dashboard access", "domain": "technical"},
    ],
    "priority": "high",
    "needs_human_flag": False,
    "summary": "User needs refund for duplicate charge and dashboard access restored.",
}

SAMPLE_DOCS = [
    {"doc": "refund-policy-v2.md",
     "content": "Refunds processed in 5-7 business days. Double-charges refunded if reported within 30 days."},
    {"doc": "dashboard-access-faq.md",
     "content": "If dashboard shows inactive: clear cache, re-login, or use force-sync in Settings."},
]


# ── Planner Agent Tests ───────────────────────────────────────────────────────
class TestPlannerAgent:

    def test_normal_ticket_returns_subtasks(self, mock_openai):
        mock_openai.return_value = json.dumps({
            "sub_tasks": [
                {"id": "t1", "description": "Refund double charge", "domain": "billing"},
                {"id": "t2", "description": "Fix dashboard", "domain": "technical"},
            ],
            "priority": "high",
            "needs_human_flag": False,
            "summary": "Refund and dashboard fix needed.",
        })
        from agents import planner_agent
        result = planner_agent.run(
            SAMPLE_TICKET_NORMAL["subject"], SAMPLE_TICKET_NORMAL["body"]
        )
        assert "task_graph" in result
        assert len(result["task_graph"]["sub_tasks"]) >= 1
        assert "duration_ms" in result

    def test_critical_ticket_sets_human_flag(self, mock_openai):
        mock_openai.return_value = json.dumps({
            "sub_tasks": [{"id": "t1", "description": "Investigate breach", "domain": "account"}],
            "priority": "critical",
            "needs_human_flag": False,  # Agent returns false, but keyword override should set True
            "summary": "Security investigation needed.",
        })
        from agents import planner_agent
        result = planner_agent.run(
            SAMPLE_TICKET_CRITICAL["subject"], SAMPLE_TICKET_CRITICAL["body"]
        )
        # Keyword "hacked" and "unauthorized" should force human flag
        assert result["task_graph"]["needs_human_flag"] is True
        assert result["task_graph"]["priority"] == "critical"


# ── Retriever Agent Tests ─────────────────────────────────────────────────────
class TestRetrieverAgent:

    def test_returns_docs_for_known_domains(self):
        from agents import retriever_agent
        result = retriever_agent.run(SAMPLE_TASK_GRAPH)
        assert "docs" in result
        assert result["doc_count"] > 0
        assert result["source"] == "mock_kb"

    def test_deduplicates_docs(self):
        graph = {
            "sub_tasks": [
                {"id": "t1", "description": "billing issue", "domain": "billing"},
                {"id": "t2", "description": "also billing", "domain": "billing"},
            ],
            "summary": "billing issue",
        }
        from agents import retriever_agent
        result = retriever_agent.run(graph)
        doc_names = [d["doc"] for d in result["docs"]]
        assert len(doc_names) == len(set(doc_names)), "Duplicate docs returned"


# ── Validator Agent Tests ─────────────────────────────────────────────────────
class TestValidatorAgent:

    def test_pass_for_good_response(self, mock_openai):
        mock_openai.return_value = json.dumps({
            "score": 88,
            "dimension_scores": {"factual_accuracy": 38, "completeness": 28, "tone": 17, "no_hallucination": 5},
            "issues": [],
            "verdict": "PASS",
            "suggestion": "",
        })
        from agents import validator_agent
        result = validator_agent.run(
            SAMPLE_TICKET_NORMAL["body"],
            "Here is your refund info and dashboard fix steps...",
            SAMPLE_DOCS,
            SAMPLE_TASK_GRAPH,
        )
        assert result["score"] == 88
        assert result["verdict"] == "PASS"

    def test_fail_for_low_score(self, mock_openai):
        mock_openai.return_value = json.dumps({
            "score": 45,
            "dimension_scores": {"factual_accuracy": 20, "completeness": 15, "tone": 8, "no_hallucination": 2},
            "issues": ["Did not address dashboard issue", "Invented refund timeline"],
            "verdict": "PASS",  # Even if LLM says pass, our code overrides based on score
            "suggestion": "Address both sub-tasks.",
        })
        from agents import validator_agent
        result = validator_agent.run(
            SAMPLE_TICKET_NORMAL["body"], "We'll look into it.",
            SAMPLE_DOCS, SAMPLE_TASK_GRAPH,
        )
        assert result["verdict"] == "FAIL"
        assert result["score"] < 75


# ── Orchestrator Integration Test ─────────────────────────────────────────────
class TestOrchestrator:

    def test_full_swarm_no_escalation(self, mock_all_agents):
        from agents.orchestrator import run_swarm
        result = run_swarm(
            ticket_id="test-001",
            user_id="user-001",
            subject=SAMPLE_TICKET_NORMAL["subject"],
            body=SAMPLE_TICKET_NORMAL["body"],
        )
        assert "ticket_id" in result
        assert "agent_traces" in result
        assert len(result["agent_traces"]) >= 4
        assert "total_duration_ms" in result

    def test_swarm_escalates_critical_ticket(self, mock_all_agents_low_confidence):
        from agents.orchestrator import run_swarm
        result = run_swarm(
            ticket_id="test-002",
            user_id="user-002",
            subject=SAMPLE_TICKET_CRITICAL["subject"],
            body=SAMPLE_TICKET_CRITICAL["body"],
        )
        assert result["escalated"] is True
        assert result["response"] is None


# ── Fixtures ──────────────────────────────────────────────────────────────────
@pytest.fixture
def mock_openai(monkeypatch):
    """Mocks the raw LLM response string."""
    responses = []
    def fake_call(*args, **kwargs):
        mock_resp = MagicMock()
        mock_resp.choices[0].message.content = responses[0] if responses else "{}"
        return mock_resp
    monkeypatch.setattr("openai.AzureOpenAI", lambda **kw: MagicMock(
        chat=MagicMock(completions=MagicMock(create=fake_call))
    ))
    return lambda v: responses.append(v) or responses.__setitem__(0, v)


@pytest.fixture(autouse=True)
def set_env(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://fake.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_KEY", "fake_key")


@pytest.fixture
def mock_all_agents(monkeypatch):
    import agents.planner_agent as pa
    import agents.retriever_agent as ra
    import agents.responder_agent as res
    import agents.validator_agent as va

    monkeypatch.setattr(pa, "run", lambda s, b: {"task_graph": SAMPLE_TASK_GRAPH, "duration_ms": 100})
    monkeypatch.setattr(ra, "run", lambda tg: {"docs": SAMPLE_DOCS, "doc_count": 2, "source": "mock_kb", "duration_ms": 50})
    monkeypatch.setattr(res, "run", lambda s, b, tg, d: {"draft": "Here is your answer.", "char_count": 22, "duration_ms": 200})
    monkeypatch.setattr(va, "run", lambda b, dr, d, tg: {"score": 88, "verdict": "PASS", "issues": [], "duration_ms": 150})


@pytest.fixture
def mock_all_agents_low_confidence(monkeypatch):
    import agents.planner_agent as pa
    import agents.retriever_agent as ra
    import agents.responder_agent as res
    import agents.validator_agent as va
    import agents.escalation_agent as ea

    critical_tg = {**SAMPLE_TASK_GRAPH, "needs_human_flag": True, "priority": "critical"}
    monkeypatch.setattr(pa, "run", lambda s, b: {"task_graph": critical_tg, "duration_ms": 100})
    monkeypatch.setattr(ra, "run", lambda tg: {"docs": SAMPLE_DOCS, "doc_count": 2, "source": "mock_kb", "duration_ms": 50})
    monkeypatch.setattr(res, "run", lambda s, b, tg, d: {"draft": "We'll look into it.", "char_count": 20, "duration_ms": 200})
    monkeypatch.setattr(va, "run", lambda b, dr, d, tg: {"score": 40, "verdict": "FAIL", "issues": ["Incomplete"], "duration_ms": 150})
    monkeypatch.setattr(ea, "run", lambda **kw: {
        "ticket_id": kw["ticket_id"], "escalation_reason": "critical_keywords_detected",
        "briefing": ["Account compromise suspected"], "recommended_action": "Lock account immediately",
        "urgency": "critical", "validator_score": 40, "escalated_at": "2026-06-07T00:00:00",
        "draft_response": "", "agent_traces": [], "duration_ms": 80,
    })
