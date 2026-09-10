import json
from unittest.mock import AsyncMock, patch

import pytest

EXTRACT_URL = "/api/v1/extract-skills"
POSITIONS_URL = "/api/v1/positions"

WELL_FORMED_JD = """
We are looking for a Senior Angular and .NET Fullstack Developer.
Required: Angular (advanced), TypeScript, C#, .NET Core.
Nice to have: Azure, SQL Server.
The candidate must have 5+ years of experience building enterprise applications.
"""

VAGUE_JD = "Need a coder."

REACT_JD = """
Senior React Frontend Developer needed.
Must have: React, TypeScript, Redux.
Nice to have: Jest, CSS, AWS.
"""

MOCK_EXTRACTION_RESPONSE = {
    "skills": [
        {"skill_name": "Angular", "category": "frontend", "is_required": True, "min_proficiency": "advanced", "confidence": "high"},
        {"skill_name": "TypeScript", "category": "frontend", "is_required": True, "min_proficiency": "intermediate", "confidence": "high"},
        {"skill_name": ".NET", "category": "backend", "is_required": True, "min_proficiency": "advanced", "confidence": "high"},
        {"skill_name": "C#", "category": "backend", "is_required": True, "min_proficiency": "intermediate", "confidence": "high"},
        {"skill_name": "Azure", "category": "cloud", "is_required": False, "min_proficiency": "beginner", "confidence": "medium"},
    ],
    "role_summary": "Senior fullstack role requiring Angular and .NET expertise for enterprise applications.",
    "suggested_seniority": "senior",
}

MOCK_REACT_RESPONSE = {
    "skills": [
        {"skill_name": "React", "category": "frontend", "is_required": True, "min_proficiency": "advanced", "confidence": "high"},
        {"skill_name": "TypeScript", "category": "frontend", "is_required": True, "min_proficiency": "advanced", "confidence": "high"},
        {"skill_name": "Redux", "category": "frontend", "is_required": True, "min_proficiency": "intermediate", "confidence": "high"},
        {"skill_name": "Jest", "category": "testing", "is_required": False, "min_proficiency": "intermediate", "confidence": "medium"},
    ],
    "role_summary": "Senior React frontend developer role with TypeScript and Redux.",
    "suggested_seniority": "senior",
}

# Returns valid JSON on second call (simulates one retry)
INVALID_THEN_VALID = [
    ("not valid json {{", {"input_tokens": 100, "output_tokens": 10, "cache_creation_input_tokens": 50, "cache_read_input_tokens": 0}),
    (json.dumps(MOCK_EXTRACTION_RESPONSE), {"input_tokens": 100, "output_tokens": 200, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 50}),
    (json.dumps({"role_summary": "test", "suggested_seniority": "senior"}), {"input_tokens": 50, "output_tokens": 50, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 50}),
]


def make_mock(response: dict):
    raw = json.dumps(response)
    usage = {"input_tokens": 100, "output_tokens": 200, "cache_creation_input_tokens": 50, "cache_read_input_tokens": 0}
    return AsyncMock(return_value=(raw, usage))


@pytest.mark.asyncio
async def test_extract_skills_well_formed_jd(client):
    with patch("app.core.llm.call_claude", make_mock(MOCK_EXTRACTION_RESPONSE)):
        response = await client.post(EXTRACT_URL, json={"jd_text": WELL_FORMED_JD})

    assert response.status_code == 200
    data = response.json()
    assert len(data["skills"]) == 5
    assert data["suggested_seniority"] == "senior"
    assert data["summary"] != ""
    skill_names = [s["skill_name"] for s in data["skills"]]
    assert "Angular" in skill_names
    assert ".NET" in skill_names


@pytest.mark.asyncio
async def test_extract_skills_react_jd(client):
    with patch("app.core.llm.call_claude", make_mock(MOCK_REACT_RESPONSE)):
        response = await client.post(EXTRACT_URL, json={"jd_text": REACT_JD})

    assert response.status_code == 200
    data = response.json()
    skill_names = [s["skill_name"] for s in data["skills"]]
    assert "React" in skill_names
    assert "TypeScript" in skill_names
    assert all(s["category"] in ("frontend", "backend", "testing", "cloud", "devops", "database", "other") for s in data["skills"])


@pytest.mark.asyncio
async def test_extract_skills_retry_path(client):
    side_effects = [
        (r, {"input_tokens": 100, "output_tokens": 10, "cache_creation_input_tokens": 50, "cache_read_input_tokens": 0})
        for r, _ in INVALID_THEN_VALID
    ]
    mock = AsyncMock(side_effect=side_effects)

    with patch("app.core.llm.call_claude", mock):
        response = await client.post(EXTRACT_URL, json={"jd_text": VAGUE_JD})

    assert response.status_code == 200
    # Claude was called at least twice (one retry)
    assert mock.call_count >= 2


@pytest.mark.asyncio
async def test_extract_and_apply_to_position(client):
    create = await client.post(POSITIONS_URL, json={
        "title": "Angular Dev",
        "department": "Engineering",
        "seniority": "senior",
        "status": "open",
        "description_raw": WELL_FORMED_JD,
        "required_skills": [],
    })
    assert create.status_code == 201
    position_id = create.json()["id"]

    with patch("app.core.llm.call_claude", make_mock(MOCK_EXTRACTION_RESPONSE)):
        response = await client.post(
            f"{POSITIONS_URL}/{position_id}/extract-skills",
            json={"jd_text": WELL_FORMED_JD},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == position_id
    assert data["ai_summary"] is not None
    assert data["ai_seniority_suggestion"] == "senior"
    assert len(data["required_skills"]) == 5
    assert all(s["source"] == "ai_extracted" for s in data["required_skills"])


@pytest.mark.asyncio
async def test_extract_and_apply_stores_history(client):
    # Create position with existing skills
    create = await client.post(POSITIONS_URL, json={
        "title": "Existing Pos",
        "department": "Engineering",
        "seniority": "mid",
        "status": "open",
        "description_raw": "Some JD",
        "required_skills": [
            {"skill_name": "Vue", "category": "frontend", "is_required": True,
             "min_proficiency": "intermediate", "confidence": "high", "source": "manual"},
        ],
    })
    position_id = create.json()["id"]

    with patch("app.core.llm.call_claude", make_mock(MOCK_EXTRACTION_RESPONSE)):
        response = await client.post(
            f"{POSITIONS_URL}/{position_id}/extract-skills",
            json={"jd_text": WELL_FORMED_JD},
        )

    assert response.status_code == 200
    # Old Vue skill should be gone, replaced by extracted skills
    skill_names = [s["skill_name"] for s in response.json()["required_skills"]]
    assert "Vue" not in skill_names
    assert "Angular" in skill_names


@pytest.mark.asyncio
async def test_extract_and_apply_position_not_found(client):
    with patch("app.core.llm.call_claude", make_mock(MOCK_EXTRACTION_RESPONSE)):
        response = await client.post(
            f"{POSITIONS_URL}/00000000-0000-0000-0000-000000000000/extract-skills",
            json={"jd_text": WELL_FORMED_JD},
        )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_extract_skills_short_jd_rejected(client):
    response = await client.post(EXTRACT_URL, json={"jd_text": "Hi"})
    assert response.status_code == 422
