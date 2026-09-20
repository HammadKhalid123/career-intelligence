from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models import JobMatch, JobMatchHistory, Resume
from models.schemas import JobDescriptionInput, MatchHistoryResponse, MatchResult
from services.llm_service import LLMServiceError, assess_job_fit, extract_job_skills
from services.matching_service import build_match_result

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.post("/analyze", response_model=MatchResult)
async def analyze_job(payload: JobDescriptionInput, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Resume).where(Resume.id == payload.resume_id))
    resume = result.scalar_one_or_none()

    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")

    if not resume.parsed_data:
        raise HTTPException(
            status_code=422, detail="Resume has not been parsed yet. Call /parse first."
        )

    try:
        job_data = await extract_job_skills(payload.job_description)
    except LLMServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))

    required_skills = job_data.get("required_skills", [])
    try:
        analysis = await assess_job_fit(
            required_skills=required_skills,
            parsed_resume=resume.parsed_data,
            resume_text=resume.raw_text or "",
            job_description=payload.job_description,
        )
    except LLMServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))

    match = build_match_result(required_skills, analysis["assessments"])

    match_record = JobMatchHistory(
        resume_id=resume.id,
        job_description=payload.job_description,
        ats_score=match["ats_score"],
        required_skills=required_skills,
        matched_skills=match["matched_skills"],
        missing_skills=match["missing_skills"],
        partial_matches=match["partial_matches"],
        evidence=match["evidence"],
        summary=analysis.get("summary", ""),
        eligibility_notes=analysis.get("eligibility_notes", []),
    )
    db.add(match_record)

    await db.commit()

    return MatchResult(
        resume_id=resume.id,
        job_description=payload.job_description,
        ats_score=match["ats_score"],
        required_skills=required_skills,
        matched_skills=match["matched_skills"],
        missing_skills=match["missing_skills"],
        partial_matches=match["partial_matches"],
        evidence=match["evidence"],
        summary=analysis.get("summary", ""),
        eligibility_notes=analysis.get("eligibility_notes", []),
    )


@router.get("/latest/{resume_id}", response_model=MatchResult)
async def get_latest_match(resume_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(JobMatchHistory)
        .where(JobMatchHistory.resume_id == resume_id)
        .order_by(desc(JobMatchHistory.created_at), desc(JobMatchHistory.id))
        .limit(1)
    )
    match_record = result.scalar_one_or_none()

    if match_record is None:
        legacy_result = await db.execute(select(JobMatch).where(JobMatch.resume_id == resume_id))
        match_record = legacy_result.scalar_one_or_none()

    if match_record is None:
        raise HTTPException(status_code=404, detail="No saved match found for this resume")

    return MatchResult(
        resume_id=match_record.resume_id,
        job_description=match_record.job_description,
        ats_score=match_record.ats_score,
        required_skills=match_record.required_skills or [],
        matched_skills=match_record.matched_skills or [],
        missing_skills=match_record.missing_skills or [],
        partial_matches=match_record.partial_matches or [],
        evidence=match_record.evidence or [],
        summary=match_record.summary or "",
        eligibility_notes=match_record.eligibility_notes or [],
    )


@router.get("/history/{resume_id}", response_model=MatchHistoryResponse)
async def get_match_history(resume_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(JobMatchHistory)
        .where(JobMatchHistory.resume_id == resume_id)
        .order_by(desc(JobMatchHistory.created_at), desc(JobMatchHistory.id))
    )
    items = [
        {
            "id": record.id,
            "created_at": record.created_at,
            "resume_id": record.resume_id,
            "job_description": record.job_description,
            "ats_score": record.ats_score,
            "required_skills": record.required_skills or [],
            "matched_skills": record.matched_skills or [],
            "missing_skills": record.missing_skills or [],
            "partial_matches": record.partial_matches or [],
            "evidence": record.evidence or [],
            "summary": record.summary or "",
            "eligibility_notes": record.eligibility_notes or [],
        }
        for record in result.scalars().all()
    ]
    return MatchHistoryResponse(resume_id=resume_id, items=items)
