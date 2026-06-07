"""
SwarmDesk AI — FastAPI Application Entry Point
Run: uvicorn api.main:app --reload --port 8000
Docs: http://localhost:8000/docs
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import tickets, health

app = FastAPI(
    title="SwarmDesk AI",
    description="Multi-agent intelligent support orchestration — Microsoft Build AI Hackathon 2026",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(tickets.router)
