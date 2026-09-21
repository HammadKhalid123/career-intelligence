from typing import Any

import httpx

from core.config import settings


class HuggingFaceInferenceEmbeddings:
    def __init__(self, model_name: str, token: str):
        self.endpoint = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{model_name}"
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}

    def _embed(self, texts: list[str]) -> list[list[float]]:
        response = httpx.post(
            self.endpoint,
            headers=self.headers,
            json={"inputs": texts, "options": {"wait_for_model": True}},
            timeout=120,
        )
        response.raise_for_status()
        embeddings: Any = response.json()
        if embeddings and isinstance(embeddings[0], list) and isinstance(embeddings[0][0], list):
            embeddings = [
                [sum(values) / len(values) for values in zip(*text_embedding)]
                for text_embedding in embeddings
            ]
        elif embeddings and isinstance(embeddings[0], (int, float)):
            embeddings = [embeddings]
        return embeddings

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embed(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._embed([text])[0]


_embedding_function: HuggingFaceInferenceEmbeddings | None = None


def get_embedding_function() -> HuggingFaceInferenceEmbeddings:
    global _embedding_function
    if _embedding_function is None:
        _embedding_function = HuggingFaceInferenceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            token=settings.HF_TOKEN,
        )
    return _embedding_function