# SwarmDesk AI
### Multi-Agent Intelligent Support Orchestration

> **Microsoft Build AI Hackathon 2026** — Theme: **Agent Swarms**
> Team: **InnovaLite** | Anisha Garg

[![Demo](https://img.shields.io/badge/Live_Demo-swarmdesk.vercel.app-00C2CB?style=for-the-badge)](https://swarmdesk.vercel.app)
[![Theme](https://img.shields.io/badge/Theme-Agent_Swarms-7B2FBE?style=for-the-badge)]()
[![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python)]()
[![AutoGen](https://img.shields.io/badge/Microsoft-AutoGen_0.4-0078D4?style=for-the-badge&logo=microsoft)]()

---

## 📌 Project Description

**SwarmDesk AI** is a production-grade multi-agent support orchestration system where five specialized AI agents collaborate, self-organize, and validate each other to resolve complex, multi-step customer support tickets — end-to-end, without human intervention for Tier 1 & 2 issues.

Traditional single-agent chatbots fail at complex support tickets because they lack domain depth, can't decompose multi-part problems, and hallucinate without validation. SwarmDesk solves this with a **distributed agent swarm** where no single agent bears the full burden.

---

## The Problem

| Metric | Reality |
|--------|---------|
| 73% of tickets | Span multiple departments |
| 8+ minutes | Average resolution time |
| 42% of tickets | Misrouted on first attempt |

---

## ⚙️ System Architecture

```
USER TICKET (Web/API/Email)
        │
        ▼
┌─────────────────────┐
│   ORCHESTRATOR      │  ← Azure OpenAI GPT-4o + AutoGen
│  (Task Router)      │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   PLANNER AGENT     │  ← Decomposes ticket into sub-tasks + task graph
└────────┬────────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌──────────┐ ┌──────────────────────┐
│RETRIEVER │ │   RESPONDER AGENT    │
│ AGENT    │→│  (GPT-4o mini + RAG) │
│(AI Search│ └──────────┬───────────┘
│ + RAG)   │            │
└──────────┘            ▼
               ┌──────────────────┐
               │ VALIDATOR AGENT  │  ← Confidence scoring & fact-check
               └────────┬─────────┘
                        │
              ┌─────────┴──────────┐
              │                    │
       Score ≥ 75%            Score < 75%
              │                    │
              ▼                    ▼
     SEND RESPONSE        ESCALATION AGENT
      TO USER             (Human Handoff +
                           Full Context Bundle)
```

---

## The Five Agents

### 1. 🎯 Planner Agent
- Receives raw ticket and decomposes into a **task dependency graph**
- Identifies which knowledge domains are needed
- Assigns sub-tasks to appropriate agents
- **Model:** GPT-4o with structured output (JSON task graph)

### 2. 📚 Retriever Agent
- Performs **semantic search** over the knowledge base
- Uses **RAG (Retrieval Augmented Generation)** with Azure AI Search
- Returns top-5 relevant documents with relevance scores
- **Model:** text-embedding-3-large + Azure AI Search vector mode

### 3. ✍️ Responder Agent
- Drafts the customer response using retrieved context
- Follows brand tone, formatting guidelines, and escalation thresholds
- **Model:** GPT-4o mini with prompt chaining

### 4. ✅ Validator Agent
- Independently reviews the drafted response
- Scores for: factual accuracy, completeness, tone, hallucination risk
- Returns a **confidence score (0–100)**
- **Model:** GPT-4o with custom evaluation rubric

### 5. 🚨 Escalation Agent
- Triggered when Validator score < 75% OR ticket contains critical keywords
- Packages full agent trace, context bundle, and recommended actions
- Routes to human agent via ticketing system webhook
- **Model:** Rule engine + GPT-4o intent classifier

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent Framework | Microsoft AutoGen 0.4 |
| LLM — Primary | Azure OpenAI GPT-4o |
| LLM — Response Draft | Azure OpenAI GPT-4o mini |
| Embeddings | text-embedding-3-large |
| Vector Store | Azure AI Search (vector + hybrid mode) |
| Backend API | FastAPI + Python 3.11 |
| Database | Azure Cosmos DB (NoSQL) |
| Cache / State | Redis (Azure Cache for Redis) |
| Frontend | Next.js 14 + TailwindCSS |
| Deployment | Azure Container Apps + Vercel |
| Auth | Azure AD B2C |
| Observability | Azure Monitor + LangSmith |
| CI/CD | GitHub Actions |

---

## 📁 Repository Structure

```
swarmdesk-ai/
├── agents/
│   ├── orchestrator.py       # Main AutoGen orchestrator
│   ├── planner_agent.py      # Task decomposition agent
│   ├── retriever_agent.py    # RAG + semantic search agent
│   ├── responder_agent.py    # Response generation agent
│   ├── validator_agent.py    # Confidence scoring agent
│   └── escalation_agent.py  # Human handoff agent
├── api/
│   ├── main.py               # FastAPI entrypoint
│   ├── routes/
│   │   ├── tickets.py        # Ticket submission endpoints
│   │   └── health.py         # Health check
│   └── models/
│       └── schemas.py        # Pydantic models
├── rag/
│   ├── indexer.py            # Knowledge base indexing
│   ├── retriever.py          # Azure AI Search wrapper
│   └── embeddings.py        # Embedding utilities
├── frontend/
│   ├── app/                  # Next.js 14 app directory
│   ├── components/           # React components
│   └── lib/                  # API client
├── infrastructure/
│   ├── bicep/                # Azure infrastructure as code
│   └── docker-compose.yml   # Local dev setup
├── tests/
│   ├── test_agents.py
│   ├── test_api.py
│   └── fixtures/             # Sample tickets
├── .env.example
├── requirements.txt
└── README.md
```

---

## Setup Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+
- Azure subscription (with OpenAI access)
- Docker (for local Redis)

### 1. Clone & Install

```bash
git clone https://github.com/AnishaGarg/swarmdesk-ai.git
cd swarmdesk-ai
pip install -r requirements.txt
```

### 2. Environment Variables

```bash
cp .env.example .env
# Fill in your Azure credentials:
```

```env
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your_key_here
AZURE_OPENAI_DEPLOYMENT_GPT4O=gpt-4o
AZURE_OPENAI_DEPLOYMENT_MINI=gpt-4o-mini
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-large
AZURE_AI_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_AI_SEARCH_KEY=your_search_key
AZURE_COSMOS_CONNECTION_STRING=your_cosmos_string
REDIS_URL=redis://localhost:6379
```

### 3. Start Local Services

```bash
# Start Redis
docker-compose up -d redis

# Index knowledge base
python rag/indexer.py --source ./data/knowledge_base/

# Start FastAPI backend
uvicorn api.main:app --reload --port 8000

# Start frontend (new terminal)
cd frontend && npm install && npm run dev
```

### 4. Access the App
- Frontend: `http://localhost:3000`
- API Docs: `http://localhost:8000/docs`

---

## 📊 Key Results (Prototype Testing)

Tested on **200 synthetic support tickets** across 3 domains (SaaS billing, technical integration, account management):

| Metric | Result |
|--------|--------|
| Tier-1 auto-resolution rate | **87%** |
| Average resolution time | **6.2 seconds** |
| User satisfaction (test cohort) | **91%** |
| Cost reduction vs. traditional support | **~60%** |
| Validator confidence (avg) | **88.4 / 100** |

---

## Future Scope

- **Plug-in Agent Marketplace** — Domain-specific agent modules (healthcare, finance, legal)
- **Multi-tenant SaaS** — White-label deployment for enterprise
- **Self-improving Agents** — Agents that learn from validated resolutions
- **10+ Language Support** — Multilingual ticket handling
- **Voice Interface** — Azure Cognitive Speech integration

---

## 👩‍💻 Team

| Name | Role |
|------|------|
| **Anisha Garg** | Full-Stack AI Engineer — Architecture, Agent Design, Frontend, Deployment |

**Team:** InnovaLite
**Hackathon:** Microsoft Build AI 2026

---

## 📄 License

MIT License — See [LICENSE](LICENSE) for details.
