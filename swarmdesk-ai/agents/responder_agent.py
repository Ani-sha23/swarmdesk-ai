"""
Responder Agent — Drafts a grounded customer support reply.
Uses GPT-4o mini with retrieved KB context + task graph.
"""
import json, os, time
from openai import AzureOpenAI

client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_KEY"],
    api_version="2024-08-01-preview",
)
GPT4O_MINI = os.environ.get("AZURE_OPENAI_DEPLOYMENT_MINI", "gpt-4o-mini")

SYSTEM_PROMPT = """You are a professional, empathetic customer support agent for SwarmDesk AI.

Your job: write a clear, helpful reply to the customer's support ticket.

STRICT RULES:
1. Only use information from the provided KNOWLEDGE BASE. Do NOT invent policies, refund amounts, timelines, or URLs.
2. Address EVERY sub-task listed in the task list — do not skip any.
3. Be warm but professional. Avoid robotic phrases like "I understand your frustration".
4. Use numbered steps where the solution requires actions.
5. Close with a clear next step or offer for follow-up.
6. Keep response under 300 words.
"""


def run(ticket_subject: str, ticket_body: str,
        task_graph: dict, docs: list[dict]) -> dict:
    t0 = time.perf_counter()

    kb_text = "\n\n".join(f"[Source: {d['doc']}]\n{d['content']}" for d in docs)
    tasks_text = "\n".join(
        f"- Task {t['id']}: {t['description']}" for t in task_graph["sub_tasks"]
    )

    user_msg = f"""CUSTOMER TICKET
Subject: {ticket_subject}
Message: {ticket_body}

TASKS TO ADDRESS:
{tasks_text}

KNOWLEDGE BASE:
{kb_text}

Write the support reply now:"""

    resp = client.chat.completions.create(
        model=GPT4O_MINI,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_msg},
        ],
        temperature=0.3,
        max_tokens=500,
    )
    draft = resp.choices[0].message.content.strip()
    elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)

    return {"draft": draft, "char_count": len(draft), "duration_ms": elapsed_ms}
