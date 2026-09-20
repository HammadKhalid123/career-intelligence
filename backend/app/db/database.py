from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


from sqlalchemy import text


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Migrate existing SQLite tables safely if columns are missing
        for alter_sql in [
            "ALTER TABLE job_matches ADD COLUMN partial_matches JSON",
            "ALTER TABLE job_matches ADD COLUMN evidence JSON",
            "ALTER TABLE job_matches ADD COLUMN summary TEXT",
            "ALTER TABLE job_matches ADD COLUMN eligibility_notes JSON",
            "ALTER TABLE job_matches ADD COLUMN updated_at DATETIME",
            "ALTER TABLE learning_content ADD COLUMN updated_at DATETIME",
        ]:
            try:
                await conn.execute(text(alter_sql))
            except Exception:
                pass

        for migrate_sql in [
            """
            INSERT INTO job_match_history
                (resume_id, job_description, ats_score, required_skills,
                 matched_skills, missing_skills, partial_matches, evidence,
                 summary, eligibility_notes, created_at)
            SELECT jm.resume_id, jm.job_description, jm.ats_score, jm.required_skills,
                   jm.matched_skills, jm.missing_skills, jm.partial_matches, jm.evidence,
                   jm.summary, jm.eligibility_notes, COALESCE(jm.updated_at, CURRENT_TIMESTAMP)
            FROM job_matches jm
            WHERE NOT EXISTS (
                SELECT 1 FROM job_match_history h WHERE h.resume_id = jm.resume_id
            )
            """,
            """
            INSERT INTO roadmap_history (resume_id, job_description, roadmap, created_at)
            SELECT rr.resume_id, rr.job_description, rr.roadmap,
                   COALESCE(rr.updated_at, CURRENT_TIMESTAMP)
            FROM roadmap_results rr
            WHERE NOT EXISTS (
                SELECT 1 FROM roadmap_history h WHERE h.resume_id = rr.resume_id
            )
            """,
        ]:
            try:
                await conn.execute(text(migrate_sql))
            except Exception:
                pass
