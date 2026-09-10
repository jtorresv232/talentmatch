import pytest
from unittest.mock import AsyncMock, patch

CANDIDATES_URL = "/api/v1/candidates"
POSITIONS_URL = "/api/v1/positions"

MOCK_RATIONALE_RESPONSE = (
    "CANDIDATE_1: Strong match with relevant experience and skills.\n"
    "CANDIDATE_2: Moderate match, missing some required skills.\n"
    "CANDIDATE_3: Weak match, significant skill gaps.\n"
)
MOCK_USAGE = {
    "input_tokens": 200, "output_tokens": 100,
    "cache_creation_input_tokens": 80, "cache_read_input_tokens": 0,
}


def make_rationale_mock():
    return AsyncMock(return_value=(MOCK_RATIONALE_RESPONSE, MOCK_USAGE))


async def create_position(client, skills):
    resp = await client.post(POSITIONS_URL, json={
        "title": "Senior React Developer",
        "department": "Engineering",
        "seniority": "senior",
        "status": "open",
        "description_raw": "Looking for senior react developer.",
        "required_skills": skills,
    })
    assert resp.status_code == 201
    return resp.json()["id"]


async def create_candidate(client, email, skills, years=5):
    resp = await client.post(CANDIDATES_URL, json={
        "full_name": f"Dev {email}",
        "email": email,
        "years_of_experience": years,
        "current_role_title": "Developer",
        "skills": skills,
    })
    assert resp.status_code == 201
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_recommend_candidates_returns_ranked_list(client):
    position_id = await create_position(client, [
        {"skill_name": "React", "category": "frontend", "is_required": True,
         "min_proficiency": "advanced", "confidence": "high", "source": "manual"},
        {"skill_name": "TypeScript", "category": "frontend", "is_required": True,
         "min_proficiency": "intermediate", "confidence": "high", "source": "manual"},
    ])

    # Best match — has both required skills at or above level
    await create_candidate(client, "best@rec.com", [
        {"skill_name": "React", "category": "frontend", "proficiency": "expert", "years_used": 5},
        {"skill_name": "TypeScript", "category": "frontend", "proficiency": "advanced", "years_used": 4},
    ], years=6)

    # Partial match — has React but not TypeScript
    await create_candidate(client, "partial@rec.com", [
        {"skill_name": "React", "category": "frontend", "proficiency": "advanced", "years_used": 3},
    ], years=5)

    # No match
    await create_candidate(client, "nomatch@rec.com", [
        {"skill_name": "Angular", "category": "frontend", "proficiency": "expert", "years_used": 6},
    ], years=5)

    with patch("app.core.llm.call_claude", make_rationale_mock()):
        response = await client.post(
            f"{POSITIONS_URL}/{position_id}/recommend-candidates",
            params={"top_n": 3},
        )

    assert response.status_code == 200
    results = response.json()
    assert len(results) <= 3
    assert results[0]["match_score"] >= results[-1]["match_score"]
    assert results[0]["candidate_name"] == "Dev best@rec.com"


@pytest.mark.asyncio
async def test_recommend_candidates_top_n_respected(client):
    position_id = await create_position(client, [
        {"skill_name": "Node.js", "category": "backend", "is_required": True,
         "min_proficiency": "intermediate", "confidence": "high", "source": "manual"},
    ])
    for i in range(4):
        await create_candidate(client, f"topn{i}@rec.com", [
            {"skill_name": "Node.js", "category": "backend", "proficiency": "advanced", "years_used": 3},
        ])

    with patch("app.core.llm.call_claude", make_rationale_mock()):
        response = await client.post(
            f"{POSITIONS_URL}/{position_id}/recommend-candidates",
            params={"top_n": 2},
        )

    assert response.status_code == 200
    assert len(response.json()) <= 2


@pytest.mark.asyncio
async def test_recommend_candidates_position_not_found(client):
    with patch("app.core.llm.call_claude", make_rationale_mock()):
        response = await client.post(
            f"{POSITIONS_URL}/00000000-0000-0000-0000-000000000000/recommend-candidates"
        )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_recommend_candidates_result_has_required_fields(client):
    position_id = await create_position(client, [
        {"skill_name": "Java", "category": "backend", "is_required": True,
         "min_proficiency": "advanced", "confidence": "high", "source": "manual"},
    ])
    await create_candidate(client, "java@rec.com", [
        {"skill_name": "Java", "category": "backend", "proficiency": "expert", "years_used": 5},
    ], years=7)

    with patch("app.core.llm.call_claude", make_rationale_mock()):
        response = await client.post(
            f"{POSITIONS_URL}/{position_id}/recommend-candidates"
        )

    assert response.status_code == 200
    rec = response.json()[0]
    assert "candidate_id" in rec
    assert "match_score" in rec
    assert "matched_skills" in rec
    assert "missing_skills" in rec
    assert "rationale" in rec
    assert "suitability_verdict" in rec
    assert rec["suitability_verdict"] in ("Strong Match", "Moderate Match", "Weak Match", "Not Suitable")


@pytest.mark.asyncio
async def test_recommend_positions_for_candidate(client):
    # Create a candidate
    candidate_id = await create_candidate(client, "recpos@rec.com", [
        {"skill_name": "React", "category": "frontend", "proficiency": "advanced", "years_used": 4},
        {"skill_name": "TypeScript", "category": "frontend", "proficiency": "intermediate", "years_used": 3},
    ], years=5)

    # Create matching position
    await create_position(client, [
        {"skill_name": "React", "category": "frontend", "is_required": True,
         "min_proficiency": "intermediate", "confidence": "high", "source": "manual"},
    ])

    with patch("app.core.llm.call_claude", make_rationale_mock()):
        response = await client.post(
            f"{CANDIDATES_URL}/{candidate_id}/recommend-positions"
        )

    assert response.status_code == 200
    results = response.json()
    assert len(results) >= 1
    assert results[0]["match_score"] >= results[-1]["match_score"]
    rec = results[0]
    assert "position_id" in rec
    assert "position_title" in rec
    assert "suitability_verdict" in rec


@pytest.mark.asyncio
async def test_recommend_positions_candidate_not_found(client):
    with patch("app.core.llm.call_claude", make_rationale_mock()):
        response = await client.post(
            f"{CANDIDATES_URL}/00000000-0000-0000-0000-000000000000/recommend-positions"
        )
    assert response.status_code == 404
