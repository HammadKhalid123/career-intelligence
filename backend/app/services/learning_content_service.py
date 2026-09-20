import json

from core.config import settings
from prompts.learning_content_prompt import (
    build_coding_challenge_prompt,
    build_flashcards_prompt,
    build_interview_questions_prompt,
    build_quiz_prompt,
)
from services.llm_service import LLMServiceError, _call_groq, _extract_json_block


async def _generate_json(prompt: str) -> dict:
    last_error = None
    for attempt in range(settings.LLM_MAX_RETRIES + 1):
        raw_output = await _call_groq(prompt, json_mode=True)
        try:
            json_str = _extract_json_block(raw_output)
            return json.loads(json_str)
        except (json.JSONDecodeError, LLMServiceError) as e:
            last_error = e
            prompt = (
                prompt
                + f"\n\nYour previous response was invalid JSON. Error: {e}. "
                "Return ONLY valid JSON this time."
            )

    raise LLMServiceError(f"Failed to get valid JSON after retries: {last_error}")


async def generate_flashcards(skill: str, count: int = 6) -> dict:
    return await _generate_json(build_flashcards_prompt(skill, count))


async def generate_quiz(skill: str, count: int = 6) -> dict:
    return await _generate_json(build_quiz_prompt(skill, count))


async def generate_coding_challenge(skill: str, count: int = 6) -> dict:
    return await _generate_json(build_coding_challenge_prompt(skill, count))


async def generate_interview_questions(skill: str, count: int = 6) -> dict:
    return await _generate_json(build_interview_questions_prompt(skill, count))