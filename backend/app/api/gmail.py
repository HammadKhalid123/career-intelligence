from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models import GmailConnection, Resume
from models.schemas import (
    GmailConnectResponse,
    GmailDraftRequest,
    GmailDraftResponse,
    GmailSendRequest,
    GmailSendResponse,
    GmailStatusResponse,
)
from services.gmail_service import (
    build_google_oauth_url,
    draft_email_from_prompt,
    exchange_google_code,
    get_google_user_email,
    gmail_token_expires_in,
    send_gmail_message,
)

router = APIRouter(prefix="/api/v1/gmail", tags=["gmail"])


@router.get("/connect", response_model=GmailConnectResponse)
async def connect_gmail(resume_id: int = Query(..., alias="resume_id"), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = result.scalar_one_or_none()
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")

    try:
        auth_url = build_google_oauth_url(resume_id)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return GmailConnectResponse(resume_id=resume_id, auth_url=auth_url)


@router.get("/callback")
async def gmail_callback(code: str | None = None, state: str | None = None, db: AsyncSession = Depends(get_db)):
    if not code or not state:
        raise HTTPException(status_code=400, detail="Google OAuth callback is missing parameters")

    try:
        resume_id = int(state)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Google OAuth state is invalid") from exc

    try:
        token_data = await exchange_google_code(code)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Unable to exchange Google OAuth code: {exc}")

    try:
        gmail_email = await get_google_user_email(token_data["access_token"])
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Unable to get Gmail account email: {exc}")

    existing = await db.execute(select(GmailConnection).where(GmailConnection.resume_id == resume_id))
    record = existing.scalar_one_or_none()

    if record is None:
        record = GmailConnection(
            resume_id=resume_id,
            gmail_email=gmail_email,
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token", ""),
            token_type=token_data.get("token_type", "Bearer"),
            expires_at=gmail_token_expires_in(token_data),
        )
        db.add(record)
    else:
        record.gmail_email = gmail_email
        record.access_token = token_data["access_token"]
        if token_data.get("refresh_token"):
            record.refresh_token = token_data["refresh_token"]
        record.token_type = token_data.get("token_type", record.token_type)
        record.expires_at = gmail_token_expires_in(token_data)

    await db.commit()

    return {
        "status": "connected",
        "resume_id": resume_id,
        "gmail_email": gmail_email,
        "message": "Gmail account connected successfully.",
    }


@router.get("/status/{resume_id}", response_model=GmailStatusResponse)
async def gmail_status(resume_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(GmailConnection).where(GmailConnection.resume_id == resume_id))
    record = result.scalar_one_or_none()

    if record is None:
        return GmailStatusResponse(connected=False, resume_id=resume_id, gmail_email=None, connected_at=None)

    return GmailStatusResponse(
        connected=True,
        resume_id=resume_id,
        gmail_email=record.gmail_email,
        connected_at=record.created_at,
    )


@router.post("/disconnect")
async def disconnect_gmail(payload: dict, db: AsyncSession = Depends(get_db)):
    resume_id = int(payload.get("resume_id"))
    result = await db.execute(select(GmailConnection).where(GmailConnection.resume_id == resume_id))
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=404, detail="No Gmail connection found for this resume")

    await db.delete(record)
    await db.commit()
    return {"status": "disconnected", "resume_id": resume_id}


@router.post("/draft", response_model=GmailDraftResponse)
async def draft_gmail_email(payload: GmailDraftRequest, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Resume).where(Resume.id == payload.resume_id))
    resume = res.scalar_one_or_none()
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")

    name = None
    if resume.parsed_data:
        name = resume.parsed_data.get("name")

    user_prompt = payload.user_prompt or "Draft a follow-up email for this job opportunity."
    try:
        draft = await draft_email_from_prompt(name, payload.job_description, user_prompt)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return GmailDraftResponse(
        resume_id=payload.resume_id,
        to=draft["to"],
        subject=draft["subject"],
        body=draft["body"],
    )


@router.post("/send", response_model=GmailSendResponse)
async def send_gmail_email(payload: GmailSendRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(GmailConnection).where(GmailConnection.resume_id == payload.resume_id))
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=404, detail="Gmail account is not connected for this resume")

    if record.expires_at and record.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Gmail access token expired. Please reconnect your account.")

    try:
        response = await send_gmail_message(record.access_token, payload.to, payload.subject, payload.body)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Gmail send failed: {exc}")

    return GmailSendResponse(
        resume_id=payload.resume_id,
        gmail_email=record.gmail_email,
        to=payload.to,
        subject=payload.subject,
        status="sent",
        message_id=response.get("id"),
    )
