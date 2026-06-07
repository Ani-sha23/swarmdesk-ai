"""
Planner Agent — Decomposes a support ticket into a structured task graph.
Uses GPT-4o with structured JSON output.
"""
import json, time
from openai import AzureOpenAI
import os

client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_KEY"],
    api_version="2024-08-01-preview",
)
GPT4O = os.environ.get("AZURE_OPENAI_DEPLOYMENT_GPT4O", "gpt-4o")

CRITICAL_KEYWORDS = {"hack", "hacked", "breach", "fraud", "legal", "lawsuit",
                     "stolen", "compromised", "unauthorized", "police", "threat"}

SYSTEM_PROMPT = """You are the Planner Agent in a multi-agent customer support system.
Your job: read the support ticket and decompose it into a structured task graph.

Return ONLY valid JSON (no markdown) with this exact shape:
{
  "sub_tasks": [
    {"id": "t1", "description": "...", "domain": "billing|technical|account|general"},
    {"id": "t2", "description": "...", "domain": "billing|technical|account|general"}
  ],
  "priority": "low|normal|high|critical",
  "needs_human_flag": true|false,
  "summary": "One concise sentence describing what the user needs overall"
}

Rules:
- Set needs_human_flag=true ONLY if ticket mentions: hacking, fraud, legal threats, data breach, account compromise.
- Set priority=critical if ticket uses words like urgent, ASAP, lawsuit, breach.
- Each sub_task should be a distinct, actionable problem to solve.
- Limit sub_tasks to max 4.
"""


def run(ticket_subject: str, ticket_body: str) -> dict:
    t0 = time.perf_counter()
    user_msg = f"TICKET SUBJECT: {ticket_subject}\n\nTICKET BODY:\n{ticket_body}"

    resp = client.chat.completions.create(
        model=GPT4O,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_msg},
        ],
        temperature=0.1,
        max_tokens=600,
        response_format={"type": "json_object"},
    )
    raw = resp.choices[0].message.content.strip()
    task_graph = json.loads(raw)
    elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)

    # Force critical flag if body contains known critical keywords
    body_lower = ticket_body.lower()
    if any(kw in body_lower for kw in CRITICAL_KEYWORDS):
        task_graph["needs_human_flag"] = True
        task_graph["priority"] = "critical"

    return {"task_graph": task_graph, "duration_ms": elapsed_ms}
