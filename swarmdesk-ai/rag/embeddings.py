"""Embedding utility — wraps Azure OpenAI text-embedding-3-large."""
import os
from openai import AzureOpenAI

client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_KEY"],
    api_version="2024-08-01-preview",
)
EMBED_MODEL = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-large")


def embed_text(text: str) -> list[float]:
    """Returns a 3072-dim embedding vector for the input text."""
    resp = client.embeddings.create(model=EMBED_MODEL, input=text[:8000])
    return resp.data[0].embedding


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Batch embed up to 16 texts at once."""
    resp = client.embeddings.create(model=EMBED_MODEL, input=texts[:16])
    return [item.embedding for item in resp.data]
