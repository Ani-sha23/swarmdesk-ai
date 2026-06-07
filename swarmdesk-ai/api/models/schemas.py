"""Pydantic v2 request/response models for SwarmDesk AI API."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TicketRequest(BaseModel):
    user_id: str = Field(..., example="user_abc123")
    subject: str = Field(..., max_length=200, example="Billing issue with Pro plan")
    body: str    = Field(..., max_length=4000,
                         example="I was charged twice this month...")
    priority: str = Field(default="normal",
                          pattern="^(low|normal|high|critical)$")


class AgentTraceItem(BaseModel):
    agent: str
    action: str
    output: str
    duration_ms: float


class TicketResponse(BaseModel):
    ticket_id: str
    user_id: str
    response: Optional[str]          # None if escalated
    escalated: bool
    confidence: int                   # 0–100
    verdict: str                      # PASS | FAIL
    agent_traces: list[AgentTraceItem]
    total_duration_ms: float
    created_at: datetime = Field(default_factory=datetime.utcnow)


class EscalationBundle(BaseModel):
    ticket_id: str
    escalation_reason: str
    briefing: list[str]
    recommended_action: str
    urgency: str
    validator_score: int
    escalated_at: str


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
