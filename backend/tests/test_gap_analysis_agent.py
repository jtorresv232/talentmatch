import pytest
from unittest.mock import AsyncMock, patch

CANDIDATES_URL = "/api/v1/candidates"
POSITIONS_URL = "/api/v1/positions"
GAP_URL = "/api/v1/gap-analysis"

MOCK_GAP_RESPONSE = (
    "- Skill: TypeScript\n"
    "  Gap: Candidate has beginner level, needs intermediate\n"
    "  Recommendation: Complete TypeScript Deep Dive course on Udemy, 4-6 weeks\n"
    "- Skill: PostgreSQL\n"
    "  Gap: Completely missing, needs intermediate\n"
    "  Recommendation: Follow PostgreSQL official tutorial and build a side project, 6-8 weeks\n",
    {"input_tokens": 150, "output_tokens": 120,
     "cache_creation_input_tokens": 60, "cache_read_input_tokens": 0},
)


async def create_candidate(client, email, skills, years=4):
    resp = await client.post(CANDIDATES_URL, json={
        "full_name": f"Dev {email}",
        "email": email,
        "years_of_experience": years,
        "current_role_title": "Developer",
        "skills": skills,
    })
    assert resp.status_code == 201
    return resp.json()["id"]


async def create_position(client, skills):
    resp = await client.post(POSITIONS_URL, json={
        "title": "Senior React Developer",
        "department": "Engineering",
        "seniority": "senior",
        "status": "open",
        "description_raw": "Looking for a senior React developer.",
        "required_skills": skills,
    })
    assert resp.status_code == 201
    return resp.json()["id"]


POSITION_SKILLS = [
    {"skill_name": "React", "category": "frontend", "is_required": True,
     "min_proficiency": "advanced", "confidence": "high", "source": "manual"},
    {"skill_name": "TypeScript", "category": "frontend", "is_required": True,
     "min_proficiency": "intermediate", "confidence": "high", "source": "manual"},
    {"skill_name": "PostgreSQL", "category": "database", "is_required": True,
     "min_proficiency": "intermediate", "confidence": "high", "source": "manual"},
]


@pytest.mark.asyncio
async def test_gap_analysis_strong_match(client):
    candidate_id = await create_candidate(client, "strong@gap.com", [
        {"skill_name": "React", "category": "frontend", "proficiency": "expert", "years_used": 5},
        {"skill_name": "TypeScript", "category": "frontend", "proficiency": "advanced", "years_used": 4},
        {"skill_name": "PostgreSQL", "category": "database", "proficiency": "advanced", "years_used": 3},
    ], years=6)
    position_id = await create_position(client, POSITION_SKILLS)

    mock = AsyncMock(return_value=("", {"input_tokens": 10, "output_tokens": 0,
                                       "cache_creation_input_tokens": 10, "cache_read_input_tokens": 0}))
    with patch("app.core.llm.call_claude", mock):
        response = await client.post(GAP_URL, json={
            "candidate_id": candidate_id,
            "position_id": position_id,
        })

    assert response.status_code == 200
    data = response.json()
    assert len(data["fully_matched"]) == 3
    assert len(data["missing"]) == 0
    assert len(data["partial"]) == 0
    assert data["verdict"] in ("Strong Match", "Moderate Match")
    assert data["score"] > 60


@pytest.mark.asyncio
async def test_gap_analysis_weak_match(client):
    candidate_id = await create_candidate(client, "weak@gap.com", [
        {"skill_name": "Angular", "category": "frontend", "proficiency": "expert", "years_used": 5},
    ], years=6)
    position_id = await create_position(client, POSITION_SKILLS)

    with patch("app.core.llm.call_claude", AsyncMock(return_value=MOCK_GAP_RESPONSE)):
        response = await client.post(GAP_URL, json={
            "candidate_id": candidate_id,
            "position_id": position_id,
        })

    assert response.status_code == 200
    data = response.json()
    assert len(data["missing"]) == 3
    assert len(data["fully_matched"]) == 0
    assert data["verdict"] in ("Weak Match", "Not Suitable")
    assert data["score"] < 40
    assert len(data["recommendations"]) > 0


@pytest.mark.asyncio
async def test_gap_analysis_partial_match(client):
    candidate_id = await create_candidate(client, "partial@gap.com", [
        {"skill_name": "React", "category": "frontend", "proficiency": "advanced", "years_used": 4},
        {"skill_name": "TypeScript", "category": "frontend", "proficiency": "beginner", "years_used": 1},
    ], years=5)
    position_id = await create_position(client, POSITION_SKILLS)

    with patch("app.core.llm.call_claude", AsyncMock(return_value=MOCK_GAP_RESPONSE)):
        response = await client.post(GAP_URL, json={
            "candidate_id": candidate_id,
            "position_id": position_id,
        })

    assert response.status_code == 200
    data = response.json()
    assert len(data["fully_matched"]) == 1   # React matched
    assert len(data["partial"]) == 1          # TypeScript below level
    assert len(data["missing"]) == 1          # PostgreSQL missing
    assert len(data["recommendations"]) > 0


@pytest.mark.asyncio
async def test_gap_analysis_candidate_not_found(client):
    position_id = await create_position(client, POSITION_SKILLS)
    response = await client.post(GAP_URL, json={
        "candidate_id": "00000000-0000-0000-0000-000000000000",
        "position_id": position_id,
    })
    assert response.status_code == 404
    assert response.json()["code"] == "candidate_not_found"


@pytest.mark.asyncio
async def test_gap_analysis_position_not_found(client):
    candidate_id = await create_candidate(client, "npos@gap.com", [
        {"skill_name": "React", "category": "frontend", "proficiency": "advanced", "years_used": 3},
    ])
    response = await client.post(GAP_URL, json={
        "candidate_id": candidate_id,
        "position_id": "00000000-0000-0000-0000-000000000000",
    })
    assert response.status_code == 404
    assert response.json()["code"] == "position_not_found"


@pytest.mark.asyncio
async def test_gap_analysis_response_has_trace(client):
    candidate_id = await create_candidate(client, "trace@gap.com", [
        {"skill_name": "React", "category": "frontend", "proficiency": "advanced", "years_used": 4},
    ], years=5)
    position_id = await create_position(client, POSITION_SKILLS)

    with patch("app.core.llm.call_claude", AsyncMock(return_value=MOCK_GAP_RESPONSE)):
        response = await client.post(GAP_URL, json={
            "candidate_id": candidate_id,
            "position_id": position_id,
        })

    assert response.status_code == 200
    trace = response.json()["trace"]
    node_names = [t["node"] for t in trace]
    assert "load_pair" in node_names
    assert "diff_skills" in node_names
    assert "assess_seniority_fit" in node_names
    assert "produce_verdict" in node_names


@pytest.mark.asyncio
async def test_batch_gap_analysis(client):
    position_id = await create_position(client, POSITION_SKILLS)
    await create_candidate(client, "batch1@gap.com", [
        {"skill_name": "React", "category": "frontend", "proficiency": "expert", "years_used": 5},
        {"skill_name": "TypeScript", "category": "frontend", "proficiency": "advanced", "years_used": 4},
        {"skill_name": "PostgreSQL", "category": "database", "proficiency": "advanced", "years_used": 3},
    ], years=6)
    await create_candidate(client, "batch2@gap.com", [
        {"skill_name": "Angular", "category": "frontend", "proficiency": "expert", "years_used": 5},
    ], years=3)

    with patch("app.core.llm.call_claude", AsyncMock(return_value=MOCK_GAP_RESPONSE)):
        response = await client.post(
            f"{POSITIONS_URL}/{position_id}/batch-gap-analysis",
            params={"top_n": 2},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["position_id"] == position_id
    assert data["position_title"] == "Senior React Developer"
    assert len(data["results"]) <= 2
    # Best candidate should be first
    assert data["results"][0]["score"] >= data["results"][-1]["score"]
