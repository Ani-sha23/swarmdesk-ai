"""
Retriever Agent — Semantic RAG retrieval using Azure AI Search + embeddings.
Falls back to mock KB when Azure Search is not configured.
"""
import os, time
from openai import AzureOpenAI

# Azure AI Search (optional - falls back to mock)
try:
    from azure.search.documents import SearchClient
    from azure.search.documents.models import VectorizableTextQuery
    from azure.core.credentials import AzureKeyCredential
    _SEARCH_AVAILABLE = True
except ImportError:
    _SEARCH_AVAILABLE = False

client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_KEY"],
    api_version="2024-08-01-preview",
)
EMBED_MODEL = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-large")

# ── Mock KB (replace with real indexed docs in Azure AI Search) ───────────────
MOCK_KB = {
    "billing": [
        {"doc": "refund-policy-v2.md",
         "content": "Refunds are processed within 5–7 business days. Double-charges are refunded automatically if reported within 30 days via the billing portal or support ticket."},
        {"doc": "billing-bug-2026-03.md",
         "content": "Known issue (March 2026): a duplicate charge affected Pro-tier users due to a payment gateway sync error. Automatic refunds are in progress. ETA: 3 business days."},
        {"doc": "invoice-faq.md",
         "content": "Invoices are emailed within 24h of charge. To download past invoices, go to Settings → Billing → Invoice History."},
    ],
    "technical": [
        {"doc": "dashboard-access-faq.md",
         "content": "If dashboard shows 'subscription inactive': (1) Clear browser cache, (2) Log out and back in, (3) If persists, trigger subscription sync via Settings → Account → Force Sync."},
        {"doc": "api-rate-limits.md",
         "content": "API rate limits: 100 req/min (Free), 1000 req/min (Pro), 10000 req/min (Enterprise). 429 errors indicate rate limit hit — implement exponential backoff."},
    ],
    "account": [
        {"doc": "subscription-states.md",
         "content": "Active subscriptions may temporarily show as 'inactive' during a billing sync (up to 15 min). Force-sync is available under Settings → Account."},
        {"doc": "security-incident-response.md",
         "content": "Suspected account compromise: immediately lock account via Settings → Security → Lock Account, reset credentials, audit access logs, notify security@swarmdesk.ai."},
        {"doc": "password-reset.md",
         "content": "To reset password: click 'Forgot Password' on login page. Link expires in 30 minutes. For SSO users, contact your IT admin."},
    ],
    "general": [
        {"doc": "support-sla.md",
         "content": "SLA commitments: Normal 24h response / 48h resolution. High 8h / 24h. Critical 2h / 8h. Priority is auto-assigned based on ticket content."},
        {"doc": "contact-channels.md",
         "content": "Support channels: Live chat (Pro+), Email support (all tiers), Phone (Enterprise only). Average wait time: < 3 min (live chat), < 4h (email)."},
    ],
}


def _embed(text: str) -> list[float]:
    resp = client.embeddings.create(model=EMBED_MODEL, input=text)
    return resp.data[0].embedding


def _azure_search(query: str, top_k: int = 5) -> list[dict]:
    """Real Azure AI Search hybrid retrieval."""
    sc = SearchClient(
        endpoint=os.environ["AZURE_AI_SEARCH_ENDPOINT"],
        index_name="swarmdesk-kb",
        credential=AzureKeyCredential(os.environ["AZURE_AI_SEARCH_KEY"]),
    )
    vector_query = VectorizableTextQuery(text=query, k_nearest_neighbors=top_k,
                                         fields="content_vector")
    results = sc.search(
        search_text=query,
        vector_queries=[vector_query],
        select=["doc", "content"],
        top=top_k,
    )
    return [{"doc": r["doc"], "content": r["content"]} for r in results]


def _mock_search(domains: list[str]) -> list[dict]:
    """Fallback: keyword domain matching."""
    docs, seen = [], set()
    for domain in domains:
        for d in MOCK_KB.get(domain, []):
            if d["doc"] not in seen:
                seen.add(d["doc"])
                docs.append(d)
    return docs


def run(task_graph: dict) -> dict:
    t0 = time.perf_counter()
    domains = list({t["domain"] for t in task_graph["sub_tasks"]})
    summary = task_graph.get("summary", "")

    use_azure = (
        _SEARCH_AVAILABLE
        and os.environ.get("AZURE_AI_SEARCH_ENDPOINT")
        and os.environ.get("AZURE_AI_SEARCH_KEY")
    )

    if use_azure:
        docs = _azure_search(summary, top_k=5)
        source = "azure_ai_search"
    else:
        docs = _mock_search(domains)
        source = "mock_kb"

    elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "docs": docs,
        "doc_count": len(docs),
        "source": source,
        "duration_ms": elapsed_ms,
    }
