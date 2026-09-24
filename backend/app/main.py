from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import agent, chat, gmail, jobs, learning, resume
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

# ✅ FIXED CORS CONFIGURATION
allowed_origins = [
    origin.strip().rstrip("/")
    for origin in settings.CORS_ORIGINS.split(",")
    if origin.strip()
]

# Vercel URL aur localhost hamesha allow karein
required_origins = [
    "https://career-intelligence-five-zeta.vercel.app",
    "https://career-intelligence.vercel.app",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

for origin in required_origins:
    if origin not in allowed_origins:
        allowed_origins.append(origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://([a-z0-9-]+\.)*vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400,
)

app.include_router(resume.router)
app.include_router(chat.router)
app.include_router(jobs.router)
app.include_router(agent.router)
app.include_router(learning.router)
app.include_router(gmail.router)


@app.get("/")
def read_root():
    return {"message": f"{settings.APP_NAME} is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}