FLASHCARDS_PROMPT = """Create {count} flashcards to help someone learn "{skill}".

Return ONLY a valid JSON object with exactly this structure, no extra text, no markdown fences:

{{
  "flashcards": [
    {{"question": "string", "answer": "string"}}
  ]
}}

Rules:
- Questions should test key concepts, not trivia.
- Answers should be concise (1-3 sentences).
- Output must be valid JSON and nothing else.
"""


def build_flashcards_prompt(skill: str, count: int = 6) -> str:
    return FLASHCARDS_PROMPT.format(skill=skill, count=count)


QUIZ_PROMPT = """Create a {count}-question multiple choice quiz to test knowledge of "{skill}".

Return ONLY a valid JSON object with exactly this structure, no extra text, no markdown fences:

{{
  "questions": [
    {{
      "question": "string",
      "options": ["string", "string", "string", "string"],
      "correct_option_index": 0,
      "explanation": "string"
    }}
  ]
}}

Rules:
- Exactly 4 options per question, only one correct.
- correct_option_index is 0-based and must point to the correct option.
- Output must be valid JSON and nothing else.
"""


def build_quiz_prompt(skill: str, count: int = 6) -> str:
    return QUIZ_PROMPT.format(skill=skill, count=count)


CODING_CHALLENGE_PROMPT = """Create {count} beginner-to-intermediate coding challenges to practice "{skill}".

Return ONLY a valid JSON object with exactly this structure, no extra text, no markdown fences:

{{
  "challenges": [
    {{
      "title": "string",
      "description": "string",
      "starter_code": "string",
      "hints": ["string", "..."]
    }}
  ]
}}

Rules:
- description must clearly state the task and expected input/output.
- starter_code is a short code skeleton in the relevant language (empty string if not applicable).
- Provide 1 to 3 hints for each challenge.
- Output must be valid JSON and nothing else.
"""


def build_coding_challenge_prompt(skill: str, count: int = 6) -> str:
  return CODING_CHALLENGE_PROMPT.format(skill=skill, count=count)


INTERVIEW_QUESTIONS_PROMPT = """Create {count} interview questions (mix of conceptual and practical) that a candidate should be ready to answer about "{skill}".

Return ONLY a valid JSON object with exactly this structure, no extra text, no markdown fences:

{{
  "questions": [
    {{"question": "string", "ideal_answer_points": ["string", "..."]}}
  ]
}}

Rules:
- ideal_answer_points must be 2-4 short bullet points of what a strong answer should cover.
- Output must be valid JSON and nothing else.
"""


def build_interview_questions_prompt(skill: str, count: int = 6) -> str:
    return INTERVIEW_QUESTIONS_PROMPT.format(skill=skill, count=count)