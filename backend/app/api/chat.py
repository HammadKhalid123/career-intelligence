from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models import Resume
from models.schemas import ChatRequest, ChatResponse, SourceChunk
from services.llm_service import LLMServiceError, call_chat_completion
from services.rag_service import build_context, retrieve_relevant_chunks

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Resume).where(Resume.id == request.resume_id))
    resume = result.scalar_one_or_none()

    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")

    chunks = retrieve_relevant_chunks(request.resume_id, request.question)

    if not chunks:
        raise HTTPException(
            status_code=422,
            detail="No indexed data found for this resume. Call /index first.",
        )

    context = build_context(chunks)

    try:
        answer = await call_chat_completion(request.question, context)
    except LLMServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))

    sources = [
        SourceChunk(
            chunk_index=chunk.metadata.get("chunk_index", 0),
            content=chunk.page_content,
        )
        for chunk in chunks
    ]

    return ChatResponse(answer=answer, sources=sources)