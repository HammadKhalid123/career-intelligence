from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from core.config import settings
from vectorstore.chroma_client import get_vectorstore


def chunk_text(text: str, resume_id: int) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.RAG_CHUNK_SIZE,
        chunk_overlap=settings.RAG_CHUNK_OVERLAP,
    )
    chunks = splitter.split_text(text)
    return [
        Document(
            page_content=chunk,
            metadata={"resume_id": resume_id, "chunk_index": i},
        )
        for i, chunk in enumerate(chunks)
    ]


def index_resume_text(resume_id: int, text: str) -> int:
    vectorstore = get_vectorstore()
    documents = chunk_text(text, resume_id)

    if not documents:
        return 0

    ids = [f"resume-{resume_id}-chunk-{i}" for i in range(len(documents))]
    vectorstore.add_documents(documents, ids=ids)
    return len(documents)


def retrieve_relevant_chunks(resume_id: int, query: str, k: int | None = None) -> list[Document]:
    vectorstore = get_vectorstore()
    k = k or settings.RAG_TOP_K
    return vectorstore.similarity_search(
        query, k=k, filter={"resume_id": resume_id}
    )


def build_context(chunks: list[Document]) -> str:
    return "\n\n".join(chunk.page_content for chunk in chunks)