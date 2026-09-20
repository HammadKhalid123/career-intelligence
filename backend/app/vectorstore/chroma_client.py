from langchain_community.vectorstores import Chroma

from core.config import settings
from services.embedding_service import get_embedding_function

_vectorstore: Chroma | None = None


def get_vectorstore() -> Chroma:
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = Chroma(
            collection_name="resumes",
            embedding_function=get_embedding_function(),
            persist_directory=settings.CHROMA_PERSIST_DIR,
        )
    return _vectorstore