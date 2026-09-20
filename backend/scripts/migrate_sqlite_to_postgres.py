"""Copy existing SQLite rows into PostgreSQL without deleting either database."""
import asyncio
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy import DateTime, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from core.config import get_async_database_url, settings
from db.models import (
    JobMatch,
    JobMatchHistory,
    LearningContent,
    LearningProgress,
    RoadmapHistory,
    RoadmapResult,
    Resume,
)


TABLES = [
    ("resumes", Resume),
    ("learning_progress", LearningProgress),
    ("job_matches", JobMatch),
    ("job_match_history", JobMatchHistory),
    ("learning_content", LearningContent),
    ("roadmap_results", RoadmapResult),
    ("roadmap_history", RoadmapHistory),
]
JSON_COLUMNS = {
    "parsed_data",
    "required_skills",
    "matched_skills",
    "missing_skills",
    "partial_matches",
    "evidence",
    "eligibility_notes",
    "content",
}


async def migrate(source: Path) -> None:
    sqlite = sqlite3.connect(source)
    sqlite.row_factory = sqlite3.Row
    engine = create_async_engine(
        get_async_database_url(settings.DATABASE_URL),
        pool_pre_ping=True,
        connect_args={"ssl": True},
    )
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with session_factory() as session:
            for table_name, model in TABLES:
                rows = sqlite.execute(f"SELECT * FROM {table_name}").fetchall()
                for row in rows:
                    values = dict(row)
                    for column in JSON_COLUMNS:
                        if isinstance(values.get(column), str):
                            values[column] = json.loads(values[column])
                    for column in model.__table__.columns:
                        value = values.get(column.name)
                        if isinstance(column.type, DateTime) and isinstance(value, str):
                            values[column.name] = datetime.fromisoformat(value)
                    with session.no_autoflush:
                        existing = await session.get(model, values["id"])
                    if existing is None:
                        session.add(
                            model(
                                **{
                                    column.name: values.get(column.name)
                                    for column in model.__table__.columns
                                }
                            )
                        )
                await session.commit()

            for table_name, _ in TABLES:
                await session.execute(
                    text(
                        f"SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), "
                        f"COALESCE(MAX(id), 1), MAX(id) IS NOT NULL) FROM {table_name}"
                    )
                )
            await session.commit()
    finally:
        sqlite.close()
        await engine.dispose()


if __name__ == "__main__":
    source_path = Path(__file__).resolve().parents[1] / "app" / "career_ai.db"
    asyncio.run(migrate(source_path))