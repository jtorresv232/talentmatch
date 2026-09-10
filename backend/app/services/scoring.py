from dataclasses import dataclass, field

from app.models.db import PROFICIENCY_ORDER, Proficiency

PROFICIENCY_SCORE: dict[str, int] = {p.value: v for p, v in PROFICIENCY_ORDER.items()}
EXPERT_SCORE = PROFICIENCY_SCORE[Proficiency.expert.value]


@dataclass
class ScoringResult:
    base_score: float
    proficiency_bonus: float
    preferred_bonus: float
    final_score: float
    matched_skills: list[dict] = field(default_factory=list)
    partial_skills: list[dict] = field(default_factory=list)
    missing_skills: list[dict] = field(default_factory=list)


def score_candidate(
    candidate_skills: list[dict],
    position_skills: list[dict],
) -> ScoringResult:
    """
    Deterministic scoring — no LLM involved.

    candidate_skills: list of dicts with keys skill_name, proficiency
    position_skills:  list of dicts with keys skill_name, min_proficiency, is_required
    """
    candidate_map = {
        s["skill_name"].lower(): PROFICIENCY_SCORE[s["proficiency"]]
        for s in candidate_skills
    }

    required = [s for s in position_skills if s["is_required"]]
    preferred = [s for s in position_skills if not s["is_required"]]

    matched_skills: list[dict] = []
    partial_skills: list[dict] = []
    missing_skills: list[dict] = []
    proficiency_deltas: list[int] = []
    max_possible_delta = 0

    for skill in required:
        name = skill["skill_name"].lower()
        required_score = PROFICIENCY_SCORE[skill["min_proficiency"]]
        candidate_score = candidate_map.get(name)

        max_possible_delta += EXPERT_SCORE - required_score

        if candidate_score is None:
            missing_skills.append(skill)
        elif candidate_score >= required_score:
            matched_skills.append(skill)
            proficiency_deltas.append(candidate_score - required_score)
        else:
            partial_skills.append(skill)
            proficiency_deltas.append(0)

    # base_score: only fully matched required skills count
    if required:
        base_score = (len(matched_skills) / len(required)) * 70
    else:
        base_score = 70.0

    # proficiency_bonus: how far above the minimum the candidate sits
    if max_possible_delta > 0:
        proficiency_bonus = (sum(proficiency_deltas) / max_possible_delta) * 20
    else:
        proficiency_bonus = 20.0 if required else 0.0

    # preferred_bonus
    if preferred:
        matched_preferred = sum(
            1 for s in preferred
            if candidate_map.get(s["skill_name"].lower()) is not None
            and candidate_map[s["skill_name"].lower()] >= PROFICIENCY_SCORE[s["min_proficiency"]]
        )
        preferred_bonus = (matched_preferred / len(preferred)) * 10
    else:
        preferred_bonus = 10.0

    final_score = round(base_score + proficiency_bonus + preferred_bonus, 2)

    return ScoringResult(
        base_score=round(base_score, 2),
        proficiency_bonus=round(proficiency_bonus, 2),
        preferred_bonus=round(preferred_bonus, 2),
        final_score=final_score,
        matched_skills=matched_skills,
        partial_skills=partial_skills,
        missing_skills=missing_skills,
    )
