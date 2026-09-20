import json

from langchain_core.tools import tool
from sqlalchemy import select

from db.database import AsyncSessionLocal
from db.models import Resume
from services.llm_service import (
    LLMServiceError,
    assess_job_fit,
    extract_job_skills,
    generate_learning_roadmap,
)
from services.matching_service import build_match_result
from services.rag_service import retrieve_relevant_chunks
from services.resource_links_service import get_learning_resources


async def _get_resume_row(resume_id: int) -> Resume | None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Resume).where(Resume.id == resume_id))
        return result.scalar_one_or_none()


@tool
async def get_resume(resume_id: int) -> str:
    """Fetch the parsed resume data (skills, experience, education, certifications)
    for a given resume_id."""
    resume = await _get_resume_row(resume_id)
    if resume is None:
        return json.dumps({"error": "Resume not found"})
    return json.dumps({"filename": resume.filename, "parsed_data": resume.parsed_data})


@tool
async def analyze_skills(resume_id: int) -> str:
    """Return the list of skills declared in the candidate's resume for a given resume_id."""
    resume = await _get_resume_row(resume_id)
    if resume is None or not resume.parsed_data:
        return json.dumps({"error": "Resume not found or not parsed yet"})
    return json.dumps({"skills": resume.parsed_data.get("skills", [])})


@tool
async def get_job_requirements(job_description: str) -> str:
    """Extract the required technical skills from a job description."""
    try:
        data = await extract_job_skills(job_description)
    except LLMServiceError as e:
        return json.dumps({"error": str(e)})
    return json.dumps(data)


@tool
async def search_vector_database(resume_id: int, query: str) -> str:
    """Search the candidate's indexed resume chunks in the vector database for
    information relevant to a query. The resume must have been indexed first."""
    chunks = retrieve_relevant_chunks(resume_id, query)
    return json.dumps({"chunks": [chunk.page_content for chunk in chunks]})


@tool
async def calculate_match_score(resume_id: int, job_description: str) -> str:
    """Compute the ATS match score between the candidate's resume and a job description.
    Returns the ats_score, matched_skills, missing_skills, and required_skills."""
    resume = await _get_resume_row(resume_id)
    if resume is None or not resume.parsed_data:
        return json.dumps({"error": "Resume not found or not parsed yet"})

    try:
        job_data = await extract_job_skills(job_description)
    except LLMServiceError as e:
        return json.dumps({"error": str(e)})

    required_skills = job_data.get("required_skills", [])
    try:
        analysis = await assess_job_fit(
            required_skills=required_skills,
            parsed_resume=resume.parsed_data,
            resume_text=resume.raw_text or "",
            job_description=job_description,
        )
    except LLMServiceError as e:
        return json.dumps({"error": str(e)})

    match = build_match_result(required_skills, analysis["assessments"])
    match["required_skills"] = required_skills
    match["summary"] = analysis.get("summary", "")
    match["eligibility_notes"] = analysis.get("eligibility_notes", [])
    return json.dumps(match)


@tool
async def create_learning_plan(missing_skills: list[str]) -> str:
    """Generate a personalized week-by-week learning roadmap for the given list of
    missing skills. This roadmap is plain, practical, bullet-point guidance only —
    it must NOT include flashcards, quizzes, or interview questions."""
    if not missing_skills:
        return json.dumps(
            {"roadmap": "No missing skills identified. This is already a strong match."}
        )
    try:
        roadmap = await generate_learning_roadmap(missing_skills)
    except LLMServiceError as e:
        return json.dumps({"error": str(e)})
    return json.dumps({"roadmap": roadmap})


@tool
async def recommend_learning_resources(skill: str) -> str:
    """Get an official documentation link and a YouTube tutorial search link for a
    given skill."""
    return json.dumps(get_learning_resources(skill))


# NOTE: get_flashcards / get_quiz / get_interview_questions were intentionally
# REMOVED from this agent's toolset (and from AGENT_TOOLS below).
#
# Reason: the Roadmap agent was calling these on its own initiative while
# building a roadmap, causing flashcards/quiz/interview-questions to leak
# into the "Additional Learning Resources" section of the roadmap output.
#
# Flashcards, quizzes, and interview questions are already served correctly
# and independently by the dedicated Learning Lab endpoints:
#   GET /api/v1/learning/flashcards
#   GET /api/v1/learning/quiz
#   GET /api/v1/learning/interview-questions
# (see routers/learning_router.py + services/learning_content_service.py)
#
# If a future agent (e.g. a general "Ask Copilot" chat agent) genuinely needs
# to offer flashcards/quiz/interview questions conversationally, re-import
# generate_flashcards / generate_quiz / generate_interview_questions from
# services.learning_content_service and register a SEPARATE tool list for
# that agent — do not add them back into AGENT_TOOLS used by the roadmap agent.


AGENT_TOOLS = [
    get_resume,
    analyze_skills,
    get_job_requirements,
    search_vector_database,
    calculate_match_score,
    create_learning_plan,
    recommend_learning_resources,
]