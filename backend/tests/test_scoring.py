import pytest
from app.services.scoring import score_candidate


def skill(name, proficiency, is_required=True):
    return {"skill_name": name, "min_proficiency": proficiency, "is_required": is_required}


def candidate_skill(name, proficiency):
    return {"skill_name": name, "proficiency": proficiency}


# ---------------------------------------------------------------------------
# Exact match
# ---------------------------------------------------------------------------

def test_exact_match_all_required():
    position_skills = [
        skill("React", "advanced"),
        skill("TypeScript", "intermediate"),
    ]
    candidate_skills = [
        candidate_skill("React", "advanced"),
        candidate_skill("TypeScript", "intermediate"),
    ]
    result = score_candidate(candidate_skills, position_skills)

    assert result.base_score == 70.0
    assert result.final_score > 70.0
    assert len(result.matched_skills) == 2
    assert len(result.partial_skills) == 0
    assert len(result.missing_skills) == 0


def test_expert_candidate_gets_proficiency_bonus():
    position_skills = [skill("React", "intermediate")]
    candidate_skills = [candidate_skill("React", "expert")]

    result = score_candidate(candidate_skills, position_skills)

    assert result.base_score == 70.0
    assert result.proficiency_bonus > 0


# ---------------------------------------------------------------------------
# Zero match
# ---------------------------------------------------------------------------

def test_zero_match():
    position_skills = [
        skill("Java", "advanced"),
        skill("Spring Boot", "intermediate"),
    ]
    candidate_skills = [
        candidate_skill("React", "expert"),
    ]
    result = score_candidate(candidate_skills, position_skills)

    assert result.base_score == 0.0
    assert result.proficiency_bonus == 0.0
    assert len(result.missing_skills) == 2
    assert len(result.matched_skills) == 0


def test_zero_match_final_score_low():
    position_skills = [skill("Java", "expert"), skill("Kafka", "advanced")]
    result = score_candidate([], position_skills)

    assert result.final_score < 20


# ---------------------------------------------------------------------------
# Partial proficiency
# ---------------------------------------------------------------------------

def test_partial_proficiency_not_counted_in_base():
    position_skills = [skill("React", "expert")]
    candidate_skills = [candidate_skill("React", "beginner")]

    result = score_candidate(candidate_skills, position_skills)

    assert result.base_score == 0.0
    assert len(result.partial_skills) == 1
    assert len(result.matched_skills) == 0


def test_partial_and_matched_mix():
    position_skills = [
        skill("React", "advanced"),
        skill("Node.js", "expert"),
        skill("PostgreSQL", "intermediate"),
    ]
    candidate_skills = [
        candidate_skill("React", "expert"),     # matched, above required
        candidate_skill("Node.js", "beginner"),  # partial, below required
        # PostgreSQL missing
    ]
    result = score_candidate(candidate_skills, position_skills)

    assert len(result.matched_skills) == 1
    assert len(result.partial_skills) == 1
    assert len(result.missing_skills) == 1
    assert result.base_score == pytest.approx(70 / 3, rel=1e-2)


# ---------------------------------------------------------------------------
# Preferred skills
# ---------------------------------------------------------------------------

def test_preferred_skills_bonus():
    position_skills = [
        skill("React", "advanced", is_required=True),
        skill("AWS", "beginner", is_required=False),
    ]
    candidate_skills = [
        candidate_skill("React", "advanced"),
        candidate_skill("AWS", "intermediate"),
    ]
    result = score_candidate(candidate_skills, position_skills)

    assert result.preferred_bonus == 10.0
    assert result.final_score == pytest.approx(100.0, rel=1e-2)


def test_preferred_skills_not_met():
    position_skills = [
        skill("React", "advanced", is_required=True),
        skill("AWS", "intermediate", is_required=False),
    ]
    candidate_skills = [candidate_skill("React", "advanced")]

    result = score_candidate(candidate_skills, position_skills)
    assert result.preferred_bonus == 0.0


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_no_required_skills_full_base_score():
    position_skills = [skill("AWS", "beginner", is_required=False)]
    result = score_candidate([], position_skills)

    assert result.base_score == 70.0


def test_skill_name_case_insensitive():
    position_skills = [skill("React", "intermediate")]
    candidate_skills = [candidate_skill("react", "advanced")]

    result = score_candidate(candidate_skills, position_skills)
    assert len(result.matched_skills) == 1


def test_final_score_capped_at_100():
    position_skills = [skill("React", "beginner")]
    candidate_skills = [candidate_skill("React", "expert")]

    result = score_candidate(candidate_skills, position_skills)
    assert result.final_score <= 100.0
