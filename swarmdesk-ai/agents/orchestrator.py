"""
SwarmDesk AI — Main Orchestrator
Runs the 5-agent pipeline: Planner → Retriever → Responder → Validator → (Escalation?)

Microsoft Build AI Hackathon 2026 | Team: InnovaLite | Anisha Garg
"""
import time, uuid
from agents import (
    planner_agent,
    retriever_agent,
    responder_agent,
    validator_agent,
    escalation_agent,
)

CONFIDENCE_THRESHOLD = 75


def run_swarm(ticket_id: str, user_id: str,
              subject: str, body: str) -> dict:
    """
    Entry point. Returns a dict with:
      - response (str | None)
      - escalated (bool)
      - confidence (int)
      - agent_traces (list)
      - total_duration_ms (float)
    """
    t_start = time.perf_counter()
    traces = []

    # ── Step 1: Planner ─────────────────────────────────────────────────────
    p = planner_agent.run(subject, body)
    task_graph = p["task_graph"]
    traces.append({
        "agent": "PlannerAgent",
        "action": "decompose_ticket",
        "output": (f"Decomposed into {len(task_graph['sub_tasks'])} sub-tasks. "
                   f"Priority: {task_graph['priority']}. "
                   f"Human flag: {task_graph['needs_human_flag']}"),
        "duration_ms": p["duration_ms"],
    })

    # ── Step 2: Retriever ────────────────────────────────────────────────────
    r = retriever_agent.run(task_graph)
    docs = r["docs"]
    traces.append({
        "agent": "RetrieverAgent",
        "action": "semantic_search",
        "output": (f"Retrieved {r['doc_count']} docs via {r['source']}: "
                   f"{[d['doc'] for d in docs]}"),
        "duration_ms": r["duration_ms"],
    })

    # ── Step 3: Responder ────────────────────────────────────────────────────
    res = responder_agent.run(subject, body, task_graph, docs)
    draft = res["draft"]
    traces.append({
        "agent": "ResponderAgent",
        "action": "draft_response",
        "output": f"Drafted {res['char_count']} char response",
        "duration_ms": res["duration_ms"],
    })

    # ── Step 4: Validator ────────────────────────────────────────────────────
    val = validator_agent.run(body, draft, docs, task_graph)
    score   = val["score"]
    verdict = val["verdict"]
    traces.append({
        "agent": "ValidatorAgent",
        "action": "score_response",
        "output": (f"Score: {score}/100 | Verdict: {verdict} | "
                   f"Issues: {val.get('issues') or 'None'}"),
        "duration_ms": val["duration_ms"],
    })

    # ── Step 5: Escalation (conditional) ────────────────────────────────────
    needs_escalation = (
        score < CONFIDENCE_THRESHOLD
        or task_graph.get("needs_human_flag", False)
    )

    final_response   = None
    escalation_bundle = None

    if needs_escalation:
        esc = escalation_agent.run(
            ticket_id=ticket_id,
            ticket_subject=subject,
            ticket_body=body,
            task_graph=task_graph,
            draft=draft,
            validator_result=val,
            agent_traces=traces,
        )
        escalation_bundle = esc
        traces.append({
            "agent": "EscalationAgent",
            "action": "human_handoff",
            "output": (f"Escalated. Reason: {esc['escalation_reason']}. "
                       f"Urgency: {esc['urgency']}"),
            "duration_ms": esc["duration_ms"],
        })
    else:
        final_response = draft

    total_ms = round((time.perf_counter() - t_start) * 1000, 1)

    return {
        "ticket_id":        ticket_id,
        "user_id":          user_id,
        "response":         final_response,
        "escalated":        needs_escalation,
        "escalation_bundle": escalation_bundle,
        "confidence":       score,
        "verdict":          verdict,
        "task_graph":       task_graph,
        "agent_traces":     traces,
        "total_duration_ms": total_ms,
    }


# ── CLI quick-test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    result = run_swarm(
        ticket_id=str(uuid.uuid4()),
        user_id="user_demo_001",
        subject="Double charge + dashboard broken",
        body=(
            "Hi, I was charged twice for my Pro subscription last month. "
            "I also can't access the analytics dashboard — it shows "
            "'subscription inactive' even though my account page says active. "
            "I need a refund and dashboard access restored ASAP."
        ),
    )

    print(f"\n{'='*60}")
    print("SWARMDESK AI — AGENT TRACE")
    print('='*60)
    for t in result["agent_traces"]:
        print(f"  [{t['agent']}]  {t['output']}  ({t['duration_ms']}ms)")

    print(f"\nCONFIDENCE : {result['confidence']}/100  ({result['verdict']})")
    print(f"ESCALATED  : {result['escalated']}")
    print(f"TOTAL TIME : {result['total_duration_ms']}ms\n")

    if result["response"]:
        print("FINAL RESPONSE:")
        print("-" * 40)
        print(result["response"])
    else:
        print("[Escalated to human agent]")
        print("BRIEFING:", result["escalation_bundle"].get("briefing"))
