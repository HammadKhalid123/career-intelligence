RESUME_EXTRACTION_PROMPT = """You are a resume parsing engine. Extract structured information from the resume text below.

Return ONLY a valid JSON object with exactly this structure, no extra text, no markdown fences:

{{
  "name": "string or null",
  "email": "string or null",
  "phone": "string or null",
  "skills": ["string", "..."],
  "experience": [
    {{
      "title": "string",
      "company": "string",
      "duration": "string",
      "description": "string"
    }}
  ],
  "education": [
    {{
      "degree": "string",
      "institution": "string",
      "year": "string"
    }}
  ],
  "certifications": [
    {{
      "name": "string",
      "provider": "string or null",
      "year": "string or null"
    }}
  ]
}}

Rules for "skills":
- Only extract items that appear under an explicit skills-related heading in the resume, such as "Technical Skills", "Skills", "Core Competencies", or similar section titles.
- Do NOT extract tools, frameworks, or technologies that only appear inside the Work Experience, Projects, or Certifications sections, even if they look like skills. Those sections describe what was used on specific projects, not the candidate's declared skill list.
- If there is no dedicated skills section in the resume, return an empty list for "skills".
- skills must be a flat list of individual skill names, exactly as written in the skills section (do not merge, rename, or reformat them).

Rules for "certifications":
- Extract every entry listed under a heading such as "Certifications", "Certifications & Languages", "Licenses & Certifications", or similar.
- "name" is the certification/course title. "provider" is the issuing platform or organization (e.g. Coursera, Google, AWS) if stated. "year" is the year if stated.
- If there is no certifications section, return an empty list.

Other rules:
- If a field is not present in the resume, use null or an empty list.
- Do not invent information that is not in the resume text.
- Output must be valid JSON and nothing else.

Resume text:
\"\"\"
{resume_text}
\"\"\"
"""


def build_extraction_prompt(resume_text: str) -> str:
    return RESUME_EXTRACTION_PROMPT.format(resume_text=resume_text)