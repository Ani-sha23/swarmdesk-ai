"""
RAG Indexer — Indexes local markdown KB files into Azure AI Search.
Run once: python rag/indexer.py --source ./data/knowledge_base/
"""
import os, argparse, glob
from pathlib import Path
from openai import AzureOpenAI

try:
    from azure.search.documents import SearchClient
    from azure.search.documents.indexes import SearchIndexClient
    from azure.search.documents.indexes.models import (
        SearchIndex, SimpleField, SearchableField,
        SearchField, SearchFieldDataType, VectorSearch,
        HnswAlgorithmConfiguration, VectorSearchProfile,
    )
    from azure.core.credentials import AzureKeyCredential
except ImportError:
    print("Install: pip install azure-search-documents")
    exit(1)

client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_KEY"],
    api_version="2024-08-01-preview",
)
EMBED_MODEL   = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-large")
SEARCH_EP     = os.environ["AZURE_AI_SEARCH_ENDPOINT"]
SEARCH_KEY    = os.environ["AZURE_AI_SEARCH_KEY"]
INDEX_NAME    = "swarmdesk-kb"
VECTOR_DIM    = 3072   # text-embedding-3-large dimension


def create_index():
    idx_client = SearchIndexClient(SEARCH_EP, AzureKeyCredential(SEARCH_KEY))
    index = SearchIndex(
        name=INDEX_NAME,
        fields=[
            SimpleField(name="id",      type=SearchFieldDataType.String, key=True),
            SimpleField(name="doc",     type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="domain",  type=SearchFieldDataType.String, filterable=True),
            SearchableField(name="content", type=SearchFieldDataType.String),
            SearchField(
                name="content_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=VECTOR_DIM,
                vector_search_profile_name="hnsw-profile",
            ),
        ],
        vector_search=VectorSearch(
            algorithms=[HnswAlgorithmConfiguration(name="hnsw-algo")],
            profiles=[VectorSearchProfile(name="hnsw-profile", algorithm_configuration_name="hnsw-algo")],
        ),
    )
    idx_client.create_or_update_index(index)
    print(f"Index '{INDEX_NAME}' created/updated.")


def embed(text: str) -> list[float]:
    resp = client.embeddings.create(model=EMBED_MODEL, input=text)
    return resp.data[0].embedding


def index_files(source_dir: str):
    sc = SearchClient(SEARCH_EP, INDEX_NAME, AzureKeyCredential(SEARCH_KEY))
    md_files = glob.glob(os.path.join(source_dir, "**/*.md"), recursive=True)
    docs = []
    for path in md_files:
        content = Path(path).read_text(encoding="utf-8")
        filename = os.path.basename(path)
        # Infer domain from filename
        domain = "general"
        for d in ["billing", "technical", "account"]:
            if d in filename.lower() or d in content.lower()[:200]:
                domain = d
                break
        vector = embed(content[:2000])   # embed first 2000 chars
        docs.append({
            "id":             filename.replace(".", "_"),
            "doc":            filename,
            "domain":         domain,
            "content":        content,
            "content_vector": vector,
        })
        print(f"  Indexed: {filename} ({domain})")

    if docs:
        sc.upload_documents(docs)
        print(f"\nIndexed {len(docs)} documents into Azure AI Search.")
    else:
        print("No .md files found.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="./data/knowledge_base/",
                        help="Path to folder containing .md KB files")
    args = parser.parse_args()
    create_index()
    index_files(args.source)
