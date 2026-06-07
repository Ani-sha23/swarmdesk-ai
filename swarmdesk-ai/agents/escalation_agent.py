"""
Escalation Agent — Packages full context and routes to a human agent.
Triggered when: Validator score < threshold OR critical keywords detected.
"""
import json, os, time
from openai import AzureOpenAI
from datetime import datetime

client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_KEY"],
    api_version="2024-08-01-preview",
)
GPT4O = os.environ.get("AZURE_OPENAI_DEPLOYMENT_GPT4O", "gpt-4o")

CRITICAL_KEYWORDS = {
    "hack", "hacked", "breach", "fraud", "legal", "lawsuit",
    "stolen", "compromised", "unauthorized", "police", "threat", "attorney"
}

SYSTEM_PROMPT = """You are the Escalation Agent. A support ticket needs human review.
Summarize the situation in 2–3 bullet points for the human agent, and provide
the single most important recommended action. Be brief and factual.

Return ONLY valid JSON:
{
  "briefing": ["bullet 1", "bullet 2", "bullet 3"],
  "recommended_action": "single most important next step",
  "urgency": "low|normal|high|critical"
}"""


def _detect_reason(ticket_body: str, score: int, needs_human_flag: bool) -> str:
    body_lower = ticket_body.lower()
    if any(kw in body_lower for kw in CRITICAL_KEYWORDS):
        return "critical_keywords_detected"
    if needs_human_flag:
        return "planner_flagged_human_needed"
    return f"validator_confidence_too_low_{score}"


def run(ticket_id: str, ticket_subject: str, ticket_body: str,
        task_graph: dict, draft: str, validator_result: dict,
        agent_traces: list[dict]) -> dict:
    t0 = time.perf_counter()

    score = validator_result.get("score", 0)
    needs_human_flag = task_graph.get("needs_human_flag", False)
    reason = _detect_reason(ticket_body, score, needs_human_flag)

    # Ask LLM to write the human-agent briefing
    user_msg = f"""TICKET ID: {ticket_id}
SUBJECT: {ticket_subject}
BODY: {ticket_body}

PLANNER SUMMARY: {task_graph.get('summary', '')}
VALIDATOR SCORE: {score}/100
VALIDATOR ISSUES: {validator_result.get('issues', [])}
ESCALATION REASON: {reason}

Write the escalation briefing for the human agent."""

    resp = client.chat.completions.create(
        model=GPT4O,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_msg},
        ],
        temperature=0.1,
        max_tokens=300,
        response_format={"type": "json_object"},
    )
    briefing_data = json.loads(resp.choices[0].message.content.strip())
    elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ticket_id": ticket_id,
        "escalation_reason": reason,
        "briefing": briefing_data.get("briefing", []),
        "recommended_action": briefing_data.get("recommended_action", ""),
        "urgency": briefing_data.get("urgency", task_graph.get("priority", "normal")),
        "validator_score": score,
        "draft_response": draft,
        "agent_traces": agent_traces,
        "escalated_at": datetime.utcnow().isoformat(),
        "duration_ms": elapsed_ms,
    }
