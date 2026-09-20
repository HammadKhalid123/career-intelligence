JOB_SKILLS_EXTRACTION_PROMPT = """You are a job description parsing engine. Extract the required technical skills from the job description below.

Return ONLY a valid JSON object with exactly this structure, no extra text, no markdown fences:

{{
  "required_skills": ["string", "..."]
}}

Rules:
- Extract explicitly requested technical tools, methods, and domain competencies (for example: statistics, machine learning, experimentation, quantitative reasoning, Python).
- Include a competency even when the job description describes it as an area of work rather than a named software tool.
- Do not include soft skills, location, degree, employer prestige, years of experience, or other eligibility conditions in required_skills.
- Do not invent skills that are not mentioned in the text.
- Deduplicate equivalent labels. For example, return "Machine Learning" only once when both "ML" and "machine learning" appear.
- required_skills must be a flat list of individual, human-readable requirement names.
- Output must be valid JSON and nothing else.

Job description:
\"\"\"
{job_description}
\"\"\"
"""


def build_job_extraction_prompt(job_description: str) -> str:
    return JOB_SKILLS_EXTRACTION_PROMPT.format(job_description=job_description)
