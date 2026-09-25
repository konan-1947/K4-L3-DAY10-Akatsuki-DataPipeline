from __future__ import annotations

from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings as LangChainOpenAIEmbeddings


class MiniLMEmbeddings(Embeddings):
    """OpenAI embedding adapter kept under the old class name for compatibility.

    The rest of the pipeline already depends on LangChain's ``Embeddings``
    interface, so switching providers only needs to happen here. The API key
    is read from ``OPENAI_API_KEY`` by LangChain OpenAI.
    """

    def __init__(self, model_name: str = "text-embedding-3-small"):
        self.model = LangChainOpenAIEmbeddings(model=model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.model.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return self.model.embed_query(text)
