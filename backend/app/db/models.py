from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=True)
    parsed_data: Mapped[dict] = mapped_column(JSON, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class LearningProgress(Base):
    __tablename__ = "learning_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resume_id: Mapped[int] = mapped_column(Integer, nullable=False)
    skill: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="not_started")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class JobMatch(Base):
    __tablename__ = "job_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resume_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    job_description: Mapped[str] = mapped_column(Text, nullable=False)
    ats_score: Mapped[float] = mapped_column(Float, nullable=False)
    required_skills: Mapped[list] = mapped_column(JSON, nullable=False)
    matched_skills: Mapped[list] = mapped_column(JSON, nullable=False)
    missing_skills: Mapped[list] = mapped_column(JSON, nullable=False)
    partial_matches: Mapped[list] = mapped_column(JSON, nullable=True, default=list)
    evidence: Mapped[list] = mapped_column(JSON, nullable=True, default=list)
    summary: Mapped[str] = mapped_column(Text, nullable=True, default="")
    eligibility_notes: Mapped[list] = mapped_column(JSON, nullable=True, default=list)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class JobMatchHistory(Base):
    __tablename__ = "job_match_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resume_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    job_description: Mapped[str] = mapped_column(Text, nullable=False)
    ats_score: Mapped[float] = mapped_column(Float, nullable=False)
    required_skills: Mapped[list] = mapped_column(JSON, nullable=False)
    matched_skills: Mapped[list] = mapped_column(JSON, nullable=False)
    missing_skills: Mapped[list] = mapped_column(JSON, nullable=False)
    partial_matches: Mapped[list] = mapped_column(JSON, nullable=True, default=list)
    evidence: Mapped[list] = mapped_column(JSON, nullable=True, default=list)
    summary: Mapped[str] = mapped_column(Text, nullable=True, default="")
    eligibility_notes: Mapped[list] = mapped_column(JSON, nullable=True, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class LearningContent(Base):
    __tablename__ = "learning_content"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resume_id: Mapped[int] = mapped_column(Integer, nullable=True)
    skill: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[dict] = mapped_column(JSON, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class RoadmapResult(Base):
    __tablename__ = "roadmap_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resume_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    job_description: Mapped[str] = mapped_column(Text, nullable=False)
    roadmap: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class RoadmapHistory(Base):
    __tablename__ = "roadmap_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resume_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    job_description: Mapped[str] = mapped_column(Text, nullable=False)
    roadmap: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
