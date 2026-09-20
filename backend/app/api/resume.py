from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models import Resume
from models.schemas import (
    ResumeIndexResponse,
    ResumeParsed,
    ResumeParseResponse,
    ResumeUploadResponse,
)
from services.llm_service import LLMServiceError, extract_resume_data
from services.rag_service import index_resume_text
from services.resume_parser import (
    ResumeValidationError,
    extract_text_from_pdf,
    save_uploaded_file,
    validate_resume_file,
)

router = APIRouter(prefix="/api/v1/resume", tags=["resume"])


@router.get("/{resume_id}/file")
async def get_resume_file(resume_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = result.scalar_one_or_none()
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")

    if not resume.file_path:
        raise HTTPException(status_code=404, detail="Resume file is not available")

    return FileResponse(
        resume.file_path,
        media_type="application/pdf",
        filename=resume.filename,
        content_disposition_type="inline",
    )


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(file: UploadFile, db: AsyncSession = Depends(get_db)):
    try:
        validate_resume_file(file)
        file_path = await save_uploaded_file(file)
        raw_text = extract_text_from_pdf(file_path)
    except ResumeValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    resume = Resume(filename=file.filename, file_path=file_path, raw_text=raw_text)
    db.add(resume)
    await db.commit()
    await db.refresh(resume)

    return resume


@router.post("/{resume_id}/parse", response_model=ResumeParseResponse)
async def parse_resume(resume_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = result.scalar_one_or_none()

    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")

    if not resume.raw_text:
        raise HTTPException(status_code=422, detail="Resume has no extracted text")

    try:
        parsed_dict = await extract_resume_data(resume.raw_text)
        parsed = ResumeParsed(**parsed_dict)
    except LLMServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))

    resume.parsed_data = parsed.model_dump()
    await db.commit()
    await db.refresh(resume)

    return ResumeParseResponse(id=resume.id, filename=resume.filename, parsed_data=parsed)


@router.post("/{resume_id}/index", response_model=ResumeIndexResponse)
async def index_resume(resume_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = result.scalar_one_or_none()

    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")

    if not resume.raw_text:
        raise HTTPException(status_code=422, detail="Resume has no extracted text")

    chunks_indexed = index_resume_text(resume.id, resume.raw_text)

    return ResumeIndexResponse(resume_id=resume.id, chunks_indexed=chunks_indexed)