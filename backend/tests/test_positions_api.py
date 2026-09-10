import pytest

BASE = "/api/v1/positions"

POSITION_PAYLOAD = {
    "title": "Senior Fullstack Engineer",
    "department": "Engineering",
    "seniority": "senior",
    "status": "open",
    "description_raw": "We are looking for a senior fullstack engineer with React and Node.js experience.",
    "required_skills": [
        {"skill_name": "React", "category": "frontend", "is_required": True, "min_proficiency": "advanced", "confidence": "high", "source": "manual"},
        {"skill_name": "Node.js", "category": "backend", "is_required": True, "min_proficiency": "intermediate", "confidence": "high", "source": "manual"},
        {"skill_name": "PostgreSQL", "category": "database", "is_required": False, "min_proficiency": "beginner", "confidence": "medium", "source": "manual"},
    ],
}


@pytest.mark.asyncio
async def test_create_position(client):
    response = await client.post(BASE, json=POSITION_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Senior Fullstack Engineer"
    assert data["seniority"] == "senior"
    assert len(data["required_skills"]) == 3
    assert "id" in data


@pytest.mark.asyncio
async def test_get_position(client):
    create = await client.post(BASE, json=POSITION_PAYLOAD)
    position_id = create.json()["id"]

    response = await client.get(f"{BASE}/{position_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == position_id
    assert data["department"] == "Engineering"
    assert len(data["required_skills"]) == 3


@pytest.mark.asyncio
async def test_get_position_not_found(client):
    response = await client.get(f"{BASE}/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert response.json()["code"] == "position_not_found"


@pytest.mark.asyncio
async def test_update_position_status(client):
    create = await client.post(BASE, json=POSITION_PAYLOAD)
    position_id = create.json()["id"]

    response = await client.patch(f"{BASE}/{position_id}", json={"status": "on_hold"})
    assert response.status_code == 200
    assert response.json()["status"] == "on_hold"
    assert len(response.json()["required_skills"]) == 3  # skills unchanged


@pytest.mark.asyncio
async def test_update_position_skills_replaced(client):
    create = await client.post(BASE, json=POSITION_PAYLOAD)
    position_id = create.json()["id"]

    new_skills = [
        {"skill_name": "Vue", "category": "frontend", "is_required": True, "min_proficiency": "intermediate", "confidence": "high", "source": "manual"},
    ]
    response = await client.patch(f"{BASE}/{position_id}", json={"required_skills": new_skills})
    assert response.status_code == 200
    skills = response.json()["required_skills"]
    assert len(skills) == 1
    assert skills[0]["skill_name"] == "Vue"


@pytest.mark.asyncio
async def test_list_positions(client):
    await client.post(BASE, json=POSITION_PAYLOAD)
    await client.post(BASE, json={**POSITION_PAYLOAD, "title": "Backend Engineer"})

    response = await client.get(BASE)
    assert response.status_code == 200
    assert len(response.json()) >= 2


@pytest.mark.asyncio
async def test_list_positions_filter_by_status(client):
    await client.post(BASE, json=POSITION_PAYLOAD)
    await client.post(BASE, json={**POSITION_PAYLOAD, "title": "Closed Role", "status": "closed"})

    response = await client.get(BASE, params={"status": "open"})
    assert response.status_code == 200
    assert all(p["status"] == "open" for p in response.json())


@pytest.mark.asyncio
async def test_list_positions_filter_by_seniority(client):
    await client.post(BASE, json=POSITION_PAYLOAD)
    await client.post(BASE, json={**POSITION_PAYLOAD, "title": "Junior Dev", "seniority": "junior"})

    response = await client.get(BASE, params={"seniority": "senior"})
    assert response.status_code == 200
    assert all(p["seniority"] == "senior" for p in response.json())


@pytest.mark.asyncio
async def test_update_position_not_found(client):
    response = await client.patch(
        f"{BASE}/00000000-0000-0000-0000-000000000000",
        json={"status": "closed"},
    )
    assert response.status_code == 404
    assert response.json()["code"] == "position_not_found"
