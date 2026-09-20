from langchain_community.embeddings import HuggingFaceEmbeddings

from core.config import settings

_embedding_function: HuggingFaceEmbeddings | None = None


def get_embedding_function() -> HuggingFaceEmbeddings:
    global _embedding_function
    if _embedding_function is None:
        _embedding_function = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL)
    return _embedding_function