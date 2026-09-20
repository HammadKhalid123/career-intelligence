from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from core.config import get_async_database_url, settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    get_async_database_url(settings.DATABASE_URL),
    echo=settings.DEBUG,
    pool_pre_ping=True,
    connect_args={"ssl": True},
)

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
        await conn.execute(text("SELECT 1"))
