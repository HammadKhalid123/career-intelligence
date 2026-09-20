from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.career_agent import run_career_agent
from db.database import get_db
from db.models import RoadmapHistory, RoadmapResult
from models.schemas import AgentRoadmapRequest, AgentRoadmapResponse, RoadmapHistoryResponse

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])


@router.post("/roadmap", response_model=AgentRoadmapResponse)
async def get_roadmap(payload: AgentRoadmapRequest, db: AsyncSession = Depends(get_db)):
    user_message = (
        f"My resume_id is {payload.resume_id}. Here is the job description:\n"
        f"{payload.job_description}\n\n"
        "Analyze how well my resume matches this job and give me a personalized "
        "learning roadmap for any missing skills."
    )

    try:
        answer = await run_career_agent(user_message)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Agent failed: {e}")

    record = RoadmapHistory(
        resume_id=payload.resume_id,
        job_description=payload.job_description,
        roadmap=answer,
    )
    db.add(record)

    await db.commit()

    return AgentRoadmapResponse(
        resume_id=payload.resume_id,
        roadmap=answer,
        job_description=payload.job_description,
    )


@router.get("/roadmap/{resume_id}", response_model=AgentRoadmapResponse)
async def get_saved_roadmap(resume_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RoadmapHistory)
        .where(RoadmapHistory.resume_id == resume_id)
        .order_by(desc(RoadmapHistory.created_at), desc(RoadmapHistory.id))
        .limit(1)
    )
    record = result.scalar_one_or_none()

    if record is None:
        legacy_result = await db.execute(select(RoadmapResult).where(RoadmapResult.resume_id == resume_id))
        record = legacy_result.scalar_one_or_none()

    if record is None:
        raise HTTPException(status_code=404, detail="No saved roadmap found for this resume")

    return AgentRoadmapResponse(
        resume_id=record.resume_id,
        roadmap=record.roadmap,
        job_description=record.job_description,
    )


@router.get("/roadmap-history/{resume_id}", response_model=RoadmapHistoryResponse)
async def get_roadmap_history(resume_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RoadmapHistory)
        .where(RoadmapHistory.resume_id == resume_id)
        .order_by(desc(RoadmapHistory.created_at), desc(RoadmapHistory.id))
    )
    items = [
        {
            "id": record.id,
            "created_at": record.created_at,
            "resume_id": record.resume_id,
            "roadmap": record.roadmap,
            "job_description": record.job_description,
        }
        for record in result.scalars().all()
    ]
    return RoadmapHistoryResponse(resume_id=resume_id, items=items)
