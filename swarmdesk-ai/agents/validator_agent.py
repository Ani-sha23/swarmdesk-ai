"""
Validator Agent — Reviews the drafted response and assigns a confidence score.
Uses GPT-4o with a custom evaluation rubric. Score < 75 triggers escalation.
"""
import json, os, time
from openai import AzureOpenAI

client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_KEY"],
    api_version="2024-08-01-preview",
)
GPT4O = os.environ.get("AZURE_OPENAI_DEPLOYMENT_GPT4O", "gpt-4o")
CONFIDENCE_THRESHOLD = int(os.environ.get("CONFIDENCE_THRESHOLD", "75"))

SYSTEM_PROMPT = """You are the Validator Agent. Your job is to quality-check a drafted support response.

Score the draft response on these 4 dimensions (points shown):
1. Factual accuracy vs. knowledge base      (0–40 pts) — Does it only use info from the KB?
2. Completeness — all sub-tasks addressed   (0–30 pts) — Did it address every task?
3. Tone & professionalism                   (0–20 pts) — Is it warm, clear, non-robotic?
4. No hallucinated policies or promises     (0–10 pts) — Did it invent anything?

Return ONLY valid JSON (no markdown):
{
  "score": <int 0-100>,
  "dimension_scores": {
    "factual_accuracy": <0-40>,
    "completeness": <0-30>,
    "tone": <0-20>,
    "no_hallucination": <0-10>
  },
  "issues": ["issue description if any", ...],
  "verdict": "PASS" | "FAIL",
  "suggestion": "One sentence on how to improve if FAIL, else empty string"
}

verdict = PASS if score >= 75, else FAIL.
"""


def run(ticket_body: str, draft: str, docs: list[dict], task_graph: dict) -> dict:
    t0 = time.perf_counter()

    kb_text  = "\n\n".join(f"[{d['doc']}]\n{d['content']}" for d in docs)
    tasks    = "\n".join(f"- {t['id']}: {t['description']}" for t in task_graph["sub_tasks"])

    user_msg = f"""ORIGINAL TICKET:
{ticket_body}

SUB-TASKS THAT MUST BE ADDRESSED:
{tasks}

KNOWLEDGE BASE (ground truth):
{kb_text}

DRAFT RESPONSE TO EVALUATE:
{draft}

Score and validate the draft now."""

    resp = client.chat.completions.create(
        model=GPT4O,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_msg},
        ],
        temperature=0.0,
        max_tokens=400,
        response_format={"type": "json_object"},
    )
    result = json.loads(resp.choices[0].message.content.strip())
    elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)

    # Clamp score just in case
    result["score"] = max(0, min(100, int(result.get("score", 0))))
    result["verdict"] = "PASS" if result["score"] >= CONFIDENCE_THRESHOLD else "FAIL"
    result["duration_ms"] = elapsed_ms
    return result
