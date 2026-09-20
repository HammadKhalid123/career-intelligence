from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import agent, chat, jobs, learning, resume
from core.config import settings
from db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resume.router)
app.include_router(chat.router)
app.include_router(jobs.router)
app.include_router(agent.router)
app.include_router(learning.router)


@app.get("/")
def read_root():
    return {"message": f"{settings.APP_NAME} is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}