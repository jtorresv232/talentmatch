import pytest

BASE = "/api/v1/candidates"

CANDIDATE_PAYLOAD = {
    "full_name": "Alice Chen",
    "email": "alice@example.com",
    "years_of_experience": 5,
    "current_role_title": "Senior Frontend Developer",
    "summary": "Experienced React developer.",
    "skills": [
        {"skill_name": "React", "category": "frontend", "proficiency": "advanced", "years_used": 4},
        {"skill_name": "TypeScript", "category": "frontend", "proficiency": "intermediate", "years_used": 3},
    ],
}


@pytest.mark.asyncio
async def test_create_candidate(client):
    response = await client.post(BASE, json=CANDIDATE_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "alice@example.com"
    assert len(data["skills"]) == 2
    assert "id" in data


@pytest.mark.asyncio
async def test_create_candidate_duplicate_email(client):
    payload = {**CANDIDATE_PAYLOAD, "email": "dup@example.com"}
    await client.post(BASE, json=payload)
    response = await client.post(BASE, json=payload)
    assert response.status_code == 409
    assert response.json()["code"] == "email_conflict"


@pytest.mark.asyncio
async def test_get_candidate(client):
    create = await client.post(BASE, json={**CANDIDATE_PAYLOAD, "email": "get@example.com"})
    candidate_id = create.json()["id"]

    response = await client.get(f"{BASE}/{candidate_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == candidate_id
    assert data["full_name"] == "Alice Chen"
    assert len(data["skills"]) == 2


@pytest.mark.asyncio
async def test_get_candidate_not_found(client):
    response = await client.get(f"{BASE}/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert response.json()["code"] == "candidate_not_found"


@pytest.mark.asyncio
async def test_update_candidate_profile(client):
    create = await client.post(BASE, json={**CANDIDATE_PAYLOAD, "email": "update@example.com"})
    candidate_id = create.json()["id"]

    response = await client.patch(f"{BASE}/{candidate_id}", json={"years_of_experience": 8})
    assert response.status_code == 200
    assert response.json()["years_of_experience"] == 8
    assert len(response.json()["skills"]) == 2  # skills unchanged


@pytest.mark.asyncio
async def test_update_candidate_skills_replaced(client):
    create = await client.post(BASE, json={**CANDIDATE_PAYLOAD, "email": "skills@example.com"})
    candidate_id = create.json()["id"]

    new_skills = [{"skill_name": "Vue", "category": "frontend", "proficiency": "beginner", "years_used": 1}]
    response = await client.patch(f"{BASE}/{candidate_id}", json={"skills": new_skills})
    assert response.status_code == 200
    skills = response.json()["skills"]
    assert len(skills) == 1
    assert skills[0]["skill_name"] == "Vue"


@pytest.mark.asyncio
async def test_delete_candidate(client):
    create = await client.post(BASE, json={**CANDIDATE_PAYLOAD, "email": "delete@example.com"})
    candidate_id = create.json()["id"]

    response = await client.delete(f"{BASE}/{candidate_id}")
    assert response.status_code == 204

    get = await client.get(f"{BASE}/{candidate_id}")
    assert get.status_code == 404


@pytest.mark.asyncio
async def test_delete_candidate_not_found(client):
    response = await client.delete(f"{BASE}/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_candidates(client):
    await client.post(BASE, json={**CANDIDATE_PAYLOAD, "email": "list1@example.com"})
    await client.post(BASE, json={**CANDIDATE_PAYLOAD, "email": "list2@example.com"})

    response = await client.get(BASE)
    assert response.status_code == 200
    assert len(response.json()) >= 2


@pytest.mark.asyncio
async def test_list_candidates_filter_by_skill_name(client):
    await client.post(BASE, json={**CANDIDATE_PAYLOAD, "email": "filter1@example.com"})

    response = await client.get(BASE, params={"skill_name": "React"})
    assert response.status_code == 200
    results = response.json()
    assert all(
        any(s["skill_name"] == "React" for s in c["skills"])
        for c in results
    )


@pytest.mark.asyncio
async def test_list_candidates_filter_by_min_proficiency(client):
    await client.post(BASE, json={**CANDIDATE_PAYLOAD, "email": "prof@example.com"})

    response = await client.get(BASE, params={"min_proficiency": "advanced"})
    assert response.status_code == 200
    for candidate in response.json():
        levels = [s["proficiency"] for s in candidate["skills"]]
        assert any(l in ("advanced", "expert") for l in levels)
