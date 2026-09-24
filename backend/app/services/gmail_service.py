import base64
import json
import re
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx

from core.config import settings
from services.llm_service import _call_groq

EMAIL_PATTERN = r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"


def build_google_oauth_url(resume_id: int) -> str:
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_REDIRECT_URI:
        raise ValueError("Google OAuth settings are not configured")

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(settings.GOOGLE_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": str(resume_id),
    }
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)


async def exchange_google_code(code: str) -> dict[str, Any]:
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise ValueError("Google OAuth credentials are not configured")

    payload = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post("https://oauth2.googleapis.com/token", data=payload)
        response.raise_for_status()
        data = response.json()
        if "access_token" not in data:
            raise ValueError(f"Google OAuth exchange failed: {data}")
        return data


async def get_google_user_email(access_token: str) -> str:
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers=headers,
        )
        response.raise_for_status()
        payload = response.json()
        email = payload.get("email") or payload.get("emailAddress")
        if not email:
            raise ValueError("Google user email could not be resolved")
        return email


async def refresh_google_token(refresh_token: str) -> dict[str, Any]:
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise ValueError("Google OAuth credentials are not configured")

    payload = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post("https://oauth2.googleapis.com/token", data=payload)
        response.raise_for_status()
        data = response.json()
        if "access_token" not in data:
            raise ValueError(f"Token refresh failed: {data}")
        return data


def extract_email_from_text(text: str | None) -> str | None:
    if not text:
        return None
    match = re.search(EMAIL_PATTERN, text)
    return match.group(0) if match else None


async def draft_email_from_prompt(
    resume_name: str | None,
    job_description: str | None,
    user_prompt: str,
) -> dict[str, str]:
    candidate_name = resume_name or "Candidate"
    prompt = (
        "You are an expert career email writer. Return ONLY valid JSON with exactly these keys: "
        "to, subject, body. "
        "The value of 'to' must be a valid recipient email address extracted from the user's request or from the job description. "
        "If there is no email address in the request, return {\"error\":\"No recipient email was found in the prompt or description.\"}. "
        "Write a concise, professional email tailored to the role. "
        f"Candidate name: {candidate_name}.\n"
        f"Job description: {job_description or 'Not provided'}.\n"
        f"User request: {user_prompt}\n"
        "Keep the email short and recruiter-friendly; include a clear subject and a polite closing."
    )

    raw = await _call_groq(prompt, json_mode=True)
    payload_text = raw.strip()
    if payload_text.startswith("```"):
        payload_text = payload_text.strip("`")
        if payload_text.lower().startswith("json"):
            payload_text = payload_text[4:]

    start = payload_text.find("{")
    end = payload_text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("AI email generation did not return valid JSON")

    parsed = json.loads(payload_text[start : end + 1])
    if "error" in parsed:
        raise ValueError(parsed["error"])

    email = parsed.get("to")
    if not email or not re.search(EMAIL_PATTERN, str(email)):
        raise ValueError("No valid recipient email was found in the email draft")

    return {
        "to": str(email),
        "subject": str(parsed.get("subject", "Application Follow-Up")),
        "body": str(parsed.get("body", "")),
    }


async def send_gmail_message(access_token: str, to_email: str, subject: str, body: str) -> dict[str, Any]:
    message = (
        "To: " + to_email + "\n"
        "Subject: " + subject + "\n"
        "MIME-Version: 1.0\n"
        "Content-Type: text/plain; charset=UTF-8\n\n"
        + body
    )
    encoded = base64.urlsafe_b64encode(message.encode("utf-8")).decode("ascii")

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json={"raw": encoded},
        )
        response.raise_for_status()
        return response.json()


def gmail_token_expires_in(tokens: dict[str, Any]) -> datetime:
    expires_in = int(tokens.get("expires_in") or 3600)
    return datetime.utcnow() + timedelta(seconds=expires_in)
