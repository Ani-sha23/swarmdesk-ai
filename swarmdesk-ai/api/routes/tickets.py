"""POST /api/tickets — Submit a ticket to the SwarmDesk agent swarm."""
import uuid
from fastapi import APIRouter, HTTPException
from api.models.schemas import TicketRequest, TicketResponse, AgentTraceItem
from agents.orchestrator import run_swarm
from datetime import datetime

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


@router.post("", response_model=TicketResponse, status_code=201)
async def submit_ticket(req: TicketRequest):
    """
    Submit a support ticket. The swarm processes it and returns either:
    - A validated response (escalated=false), or
    - An escalation notification (escalated=true)
    """
    ticket_id = str(uuid.uuid4())

    try:
        result = run_swarm(
            ticket_id=ticket_id,
            user_id=req.user_id,
            subject=req.subject,
            body=req.body,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Swarm processing error: {str(e)}")

    return TicketResponse(
        ticket_id=result["ticket_id"],
        user_id=result["user_id"],
        response=result["response"],
        escalated=result["escalated"],
        confidence=result["confidence"],
        verdict=result["verdict"],
        agent_traces=[AgentTraceItem(**t) for t in result["agent_traces"]],
        total_duration_ms=result["total_duration_ms"],
        created_at=datetime.utcnow(),
    )


@router.get("/{ticket_id}", tags=["tickets"])
async def get_ticket_status(ticket_id: str):
    """
    Get status of a previously submitted ticket.
    (In production this reads from Cosmos DB.)
    """
    # TODO: query Cosmos DB for persisted ticket
    return {"ticket_id": ticket_id, "status": "resolved", "note": "Connect Cosmos DB to enable persistence."}
