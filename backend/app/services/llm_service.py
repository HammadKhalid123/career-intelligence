import asyncio
import json

import httpx

from core.config import settings
from prompts.job_extraction_prompt import build_job_extraction_prompt
from prompts.job_match_prompt import build_job_match_prompt
from prompts.resume_extraction_prompt import build_extraction_prompt

RATE_LIMIT_MAX_RETRIES = 3
RATE_LIMIT_DEFAULT_WAIT_SECONDS = 5


class LLMServiceError(Exception):
    pass


def _extract_json_block(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json"):
            raw = raw[4:]
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1:
        raise LLMServiceError("No JSON object found in LLM response")
    return raw[start : end + 1]


async def _call_groq(
    prompt: str,
    system_instruction: str | None = None,
    json_mode: bool = False,
) -> str:
    if not settings.GROQ_API_KEY:
        raise LLMServiceError("GROQ_API_KEY is not set")

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": settings.GROQ_MODEL,
        "messages": messages,
        "temperature": 0.2,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    url = f"{settings.GROQ_BASE_URL}/chat/completions"

    last_error = None

    for attempt in range(RATE_LIMIT_MAX_RETRIES + 1):
        async with httpx.AsyncClient(timeout=60) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                if (
                    json_mode
                    and e.response.status_code == 400
                    and "json_validate_failed" in e.response.text
                ):
                    fallback_payload = {key: value for key, value in payload.items()}
                    fallback_payload.pop("response_format", None)
                    fallback_payload["messages"] = [
                        *messages[:-1],
                        {
                            "role": "user",
                            "content": (
                                f"{prompt}\n\nReturn only one valid JSON object. "
                                "Do not use markdown or explanatory text."
                            ),
                        },
                    ]
                    response = await client.post(
                        url, headers=headers, json=fallback_payload
                    )
                    response.raise_for_status()
                    payload = fallback_payload
                    json_mode = False
                    break
                if (
                    e.response.status_code in (429, 503)
                    and attempt < RATE_LIMIT_MAX_RETRIES
                ):
                    last_error = e
                    await asyncio.sleep(RATE_LIMIT_DEFAULT_WAIT_SECONDS)
                    continue
                raise LLMServiceError(
                    f"Groq API error {e.response.status_code}: {e.response.text}"
                )
            except httpx.HTTPError as e:
                raise LLMServiceError(
                    f"Groq request failed: {type(e).__name__}: {e!r}"
                )

        data = response.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            raise LLMServiceError(f"Unexpected Groq response shape: {data}")

    raise LLMServiceError(f"Groq rate limit exceeded after retries: {last_error}")


RAG_ANSWER_SYSTEM_PROMPT = (
    "You are a career assistant answering questions about a candidate's resume. "
    "Only use the information in the provided context. "
    "If the answer is not present in the context, say you don't have enough "
    "information to answer that."
)


async def call_chat_completion(question: str, context: str) -> str:
    user_prompt = f"Context:\n{context}\n\nQuestion: {question}"
    return await _call_groq(user_prompt, system_instruction=RAG_ANSWER_SYSTEM_PROMPT)


async def extract_resume_data(resume_text: str) -> dict:
    prompt = build_extraction_prompt(resume_text)

    last_error = None
    for attempt in range(settings.LLM_MAX_RETRIES + 1):
        raw_output = await _call_groq(prompt, json_mode=True)
        try:
            json_str = _extract_json_block(raw_output)
            parsed = json.loads(json_str)
            return parsed
        except (json.JSONDecodeError, LLMServiceError) as e:
            last_error = e
            prompt = (
                build_extraction_prompt(resume_text)
                + f"\n\nYour previous response was invalid JSON. Error: {e}. "
                "Return ONLY valid JSON this time."
            )

    raise LLMServiceError(f"Failed to get valid JSON after retries: {last_error}")


async def extract_job_skills(job_description: str) -> dict:
    prompt = build_job_extraction_prompt(job_description)

    last_error = None
    for attempt in range(settings.LLM_MAX_RETRIES + 1):
        raw_output = await _call_groq(prompt, json_mode=True)
        try:
            json_str = _extract_json_block(raw_output)
            parsed = json.loads(json_str)
            return parsed
        except (json.JSONDecodeError, LLMServiceError) as e:
            last_error = e
            prompt = (
                build_job_extraction_prompt(job_description)
                + f"\n\nYour previous response was invalid JSON. Error: {e}. "
                "Return ONLY valid JSON this time."
            )

    raise LLMServiceError(f"Failed to get valid JSON after retries: {last_error}")


async def assess_job_fit(
    required_skills: list[str],
    parsed_resume: dict,
    resume_text: str,
    job_description: str,
) -> dict:
    """Ask the LLM for evidence-backed requirement classifications, not a score."""
    prompt = build_job_match_prompt(
        required_skills_json=json.dumps(required_skills),
        parsed_resume_json=json.dumps(parsed_resume),
        resume_text=resume_text,
        job_description=job_description,
    )
    last_error = None
    for attempt in range(settings.LLM_MAX_RETRIES + 1):
        raw_output = await _call_groq(prompt, json_mode=True)
        try:
            result = json.loads(_extract_json_block(raw_output))
            if not isinstance(result.get("assessments"), list):
                raise LLMServiceError("Match analysis did not include assessments")
            return result
        except (json.JSONDecodeError, LLMServiceError) as e:
            last_error = e
            prompt += f"\n\nPrevious response was invalid ({e}). Return the required JSON only."
    raise LLMServiceError(f"Failed to analyze job fit after retries: {last_error}")


async def generate_learning_roadmap(missing_skills: list[str]) -> str:
    skills_text = ", ".join(missing_skills) if missing_skills else "no missing skills"

    prompt = (
        "Create a concise week-by-week learning roadmap (max 4 weeks) to help a candidate "
        f"learn the following missing skills: {skills_text}. "
        "Keep it practical and actionable, using short bullet points."
    )
    return await _call_groq(prompt)
