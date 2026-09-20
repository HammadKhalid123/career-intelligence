from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models import LearningContent, LearningProgress
from models.schemas import (
    CodingChallengeResponse,
    FlashcardsResponse,
    InterviewQuestionsResponse,
    LearningResourcesResponse,
    ProgressItem,
    ProgressResponse,
    ProgressUpdateRequest,
    QuizResponse,
    SavedLearningContentItem,
    SavedLearningContentResponse,
)
from services.learning_content_service import (
    generate_coding_challenge,
    generate_flashcards,
    generate_interview_questions,
    generate_quiz,
)
from services.llm_service import LLMServiceError
from services.resource_links_service import get_learning_resources

router = APIRouter(prefix="/api/v1/learning", tags=["learning"])


async def _save_learning_content(
    db: AsyncSession, resume_id: int | None, skill: str, content_type: str, content: dict
) -> None:
    if resume_id is None:
        return

    result = await db.execute(
        select(LearningContent).where(
            LearningContent.resume_id == resume_id,
            LearningContent.skill == skill,
            LearningContent.content_type == content_type,
        )
    )
    record = result.scalar_one_or_none()

    if record is None:
        record = LearningContent(
            resume_id=resume_id, skill=skill, content_type=content_type, content=content
        )
        db.add(record)
    else:
        record.content = content
        record.updated_at = datetime.utcnow()

    await db.commit()



@router.get("/resources", response_model=LearningResourcesResponse)
async def resources(skill: str = Query(...)):
    data = get_learning_resources(skill)
    return LearningResourcesResponse(**data)


@router.get("/flashcards", response_model=FlashcardsResponse)
async def flashcards(
    skill: str = Query(...),
    count: int = Query(6, ge=1, le=15),
    resume_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    try:
        data = await generate_flashcards(skill, count)
    except LLMServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))

    await _save_learning_content(db, resume_id, skill, "flashcards", data)

    return FlashcardsResponse(skill=skill, flashcards=data.get("flashcards", []))


@router.get("/quiz", response_model=QuizResponse)
async def quiz(
    skill: str = Query(...),
    count: int = Query(6, ge=1, le=15),
    resume_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    try:
        data = await generate_quiz(skill, count)
    except LLMServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))

    await _save_learning_content(db, resume_id, skill, "quiz", data)

    return QuizResponse(skill=skill, questions=data.get("questions", []))


@router.get("/coding-challenge", response_model=CodingChallengeResponse)
async def coding_challenge(
    skill: str = Query(...),
    count: int = Query(6, ge=1, le=15),
    resume_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    try:
        data = await generate_coding_challenge(skill, count)
    except LLMServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))

    await _save_learning_content(db, resume_id, skill, "coding_challenge", data)

    return CodingChallengeResponse(skill=skill, challenges=data.get("challenges", []))


@router.get("/interview-questions", response_model=InterviewQuestionsResponse)
async def interview_questions(
    skill: str = Query(...),
    count: int = Query(6, ge=1, le=15),
    resume_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    try:
        data = await generate_interview_questions(skill, count)
    except LLMServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))

    await _save_learning_content(db, resume_id, skill, "interview_questions", data)

    return InterviewQuestionsResponse(skill=skill, questions=data.get("questions", []))


@router.get("/saved/{resume_id}", response_model=SavedLearningContentResponse)
async def get_saved_content(resume_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(LearningContent)
        .where(LearningContent.resume_id == resume_id)
        .order_by(LearningContent.updated_at.desc())
    )
    records = result.scalars().all()

    items = [
        SavedLearningContentItem(
            skill=r.skill,
            content_type=r.content_type,
            content=r.content,
            updated_at=r.updated_at,
        )
        for r in records
    ]

    return SavedLearningContentResponse(resume_id=resume_id, items=items)


@router.post("/progress", response_model=ProgressItem)

async def update_progress(payload: ProgressUpdateRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(LearningProgress).where(
            LearningProgress.resume_id == payload.resume_id,
            LearningProgress.skill == payload.skill,
        )
    )
    record = result.scalar_one_or_none()

    if record is None:
        record = LearningProgress(
            resume_id=payload.resume_id, skill=payload.skill, status=payload.status
        )
        db.add(record)
    else:
        record.status = payload.status

    await db.commit()
    await db.refresh(record)

    return ProgressItem(skill=record.skill, status=record.status, updated_at=record.updated_at)


@router.get("/progress/{resume_id}", response_model=ProgressResponse)
async def get_progress(resume_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(LearningProgress).where(LearningProgress.resume_id == resume_id)
    )
    records = result.scalars().all()
    progress = [
        ProgressItem(skill=r.skill, status=r.status, updated_at=r.updated_at)
        for r in records
    ]
    return ProgressResponse(resume_id=resume_id, progress=progress)