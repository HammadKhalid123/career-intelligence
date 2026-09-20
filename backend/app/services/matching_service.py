from collections.abc import Iterable

VALID_STATUSES = {"direct_match", "evidence_match", "partial_match", "missing"}
STATUS_WEIGHT = {"direct_match": 1.0, "evidence_match": 1.0, "partial_match": 0.5, "missing": 0.0}


def _normalise(value: str) -> str:
    return " ".join(value.lower().strip().split())


def build_match_result(required_skills: list[str], assessments: Iterable[dict]) -> dict:
    """Validate LLM classifications and derive a reproducible score from them.

    The model may explain evidence, but it cannot add requirements or invent the score.
    Every extracted job requirement is represented exactly once in the final result.
    """
    by_requirement = {
        _normalise(item.get("requirement", "")): item
        for item in assessments
        if isinstance(item, dict) and isinstance(item.get("requirement"), str)
    }
    matched_skills, partial_matches, missing_skills, evidence = [], [], [], []
    total_weight = 0.0

    for requirement in required_skills:
        item = by_requirement.get(_normalise(requirement), {})
        status = item.get("status")
        if status not in VALID_STATUSES:
            status = "missing"
        explanation = item.get("evidence", "")
        if not isinstance(explanation, str):
            explanation = ""

        total_weight += STATUS_WEIGHT[status]
        if status in {"direct_match", "evidence_match"}:
            matched_skills.append(requirement)
        elif status == "partial_match":
            partial_matches.append(requirement)
        else:
            missing_skills.append(requirement)
        evidence.append(
            {"requirement": requirement, "status": status, "evidence": explanation.strip()}
        )

    score = round((total_weight / len(required_skills)) * 100, 2) if required_skills else 0.0
    return {
        "ats_score": score,
        "matched_skills": matched_skills,
        "partial_matches": partial_matches,
        "missing_skills": missing_skills,
        "evidence": evidence,
    }
