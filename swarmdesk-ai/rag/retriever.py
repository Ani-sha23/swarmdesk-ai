"""
Azure AI Search wrapper for semantic + vector hybrid retrieval.
Used by retriever_agent.py.
"""
import os
from openai import AzureOpenAI

try:
    from azure.search.documents import SearchClient
    from azure.search.documents.models import VectorizableTextQuery
    from azure.core.credentials import AzureKeyCredential
    _AVAILABLE = True
except ImportError:
    _AVAILABLE = False

oa_client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_KEY"],
    api_version="2024-08-01-preview",
)
EMBED_MODEL = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-large")


def search(query: str, top_k: int = 5) -> list[dict]:
    """Hybrid (keyword + vector) search over the indexed KB."""
    if not _AVAILABLE:
        raise ImportError("azure-search-documents not installed.")

    sc = SearchClient(
        endpoint=os.environ["AZURE_AI_SEARCH_ENDPOINT"],
        index_name="swarmdesk-kb",
        credential=AzureKeyCredential(os.environ["AZURE_AI_SEARCH_KEY"]),
    )
    vq = VectorizableTextQuery(text=query, k_nearest_neighbors=top_k,
                                fields="content_vector")
    results = sc.search(
        search_text=query,
        vector_queries=[vq],
        select=["doc", "content", "domain"],
        top=top_k,
    )
    return [{"doc": r["doc"], "content": r["content"], "domain": r["domain"]}
            for r in results]
