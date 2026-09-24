from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class ResumeUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    uploaded_at: datetime
    message: str = "Resume uploaded successfully"


class ResumeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    raw_text: str | None = None
    uploaded_at: datetime


class ExperienceItem(BaseModel):
    title: str | None = None
    company: str | None = None
    duration: str | None = None
    description: str | None = None


class EducationItem(BaseModel):
    degree: str | None = None
    institution: str | None = None
    year: str | None = None


class CertificationItem(BaseModel):
    name: str
    provider: str | None = None
    year: str | None = None


class ResumeParsed(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    skills: list[str] = []
    experience: list[ExperienceItem] = []
    education: list[EducationItem] = []
    certifications: list[CertificationItem] = []


class ResumeParseResponse(BaseModel):
    id: int
    filename: str
    parsed_data: ResumeParsed


class ResumeIndexResponse(BaseModel):
    resume_id: int
    chunks_indexed: int


class ChatRequest(BaseModel):
    resume_id: int
    question: str


class SourceChunk(BaseModel):
    chunk_index: int
    content: str

class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]


class JobDescriptionInput(BaseModel):
    resume_id: int
    job_description: str


class GmailConnectResponse(BaseModel):
    resume_id: int
    auth_url: str


class GmailStatusResponse(BaseModel):
    connected: bool
    resume_id: int
    gmail_email: str | None = None
    connected_at: datetime | None = None


class GmailDraftRequest(BaseModel):
    resume_id: int
    job_description: str
    user_prompt: str | None = None


class GmailDraftResponse(BaseModel):
    resume_id: int
    to: str
    subject: str
    body: str


class GmailSendRequest(BaseModel):
    resume_id: int
    to: str
    subject: str
    body: str


class GmailSendResponse(BaseModel):
    resume_id: int
    gmail_email: str
    to: str
    subject: str
    status: str
    message_id: str | None = None


class MatchResult(BaseModel):
    resume_id: int
    ats_score: float
    required_skills: list[str]
    matched_skills: list[str]
    missing_skills: list[str]
    partial_matches: list[str] = []
    evidence: list[dict[str, str]] = []
    summary: str = ""
    eligibility_notes: list[str] = []
    job_description: str | None = None


class MatchHistoryItem(MatchResult):
    id: int
    created_at: datetime


class MatchHistoryResponse(BaseModel):
    resume_id: int
    items: list[MatchHistoryItem]


class AgentRoadmapRequest(BaseModel):
    resume_id: int
    job_description: str


class AgentRoadmapResponse(BaseModel):
    resume_id: int
    roadmap: str
    job_description: str | None = None


class RoadmapHistoryItem(AgentRoadmapResponse):
    id: int
    created_at: datetime


class RoadmapHistoryResponse(BaseModel):
    resume_id: int
    items: list[RoadmapHistoryItem]


class FlashcardItem(BaseModel):
    question: str
    answer: str


class FlashcardsResponse(BaseModel):
    skill: str
    flashcards: list[FlashcardItem]


class QuizQuestionItem(BaseModel):
    question: str
    options: list[str]
    correct_option_index: int
    explanation: str



class QuizResponse(BaseModel):
    skill: str
    questions: list[QuizQuestionItem]


class CodingChallengeItem(BaseModel):
    title: str
    description: str
    starter_code: str
    hints: list[str]


class CodingChallengeResponse(BaseModel):
    skill: str
    challenges: list[CodingChallengeItem]


class InterviewQuestionItem(BaseModel):
    question: str
    ideal_answer_points: list[str]


class InterviewQuestionsResponse(BaseModel):
    skill: str
    questions: list[InterviewQuestionItem]


class LearningResourceItem(BaseModel):
    title: str
    resource_type: str
    url: str


class LearningResourcesResponse(BaseModel):
    skill: str
    documentation_search_url: str
    video_search_url: str
    resources: list[LearningResourceItem] = []


class ProgressUpdateRequest(BaseModel):
    resume_id: int
    skill: str
    status: Literal["not_started", "in_progress", "completed"]


class ProgressItem(BaseModel):
    skill: str
    status: str
    updated_at: datetime




class ProgressResponse(BaseModel):
    resume_id: int
    progress: list[ProgressItem]



class SavedLearningContentItem(BaseModel):
    skill: str
    content_type: str
    content: dict
    updated_at: datetime


class SavedLearningContentResponse(BaseModel):
    resume_id: int
    items: list[SavedLearningContentItem]


class ErrorResponse(BaseModel):
    error: bool = True
    message: str
    code: str
