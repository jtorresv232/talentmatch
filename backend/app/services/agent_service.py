import uuid

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.skill_extraction_graph import skill_extraction_graph
from app.core.errors import not_found
from app.models.db import ExtractionHistory, Position, PositionSkill
from app.schemas.api import SkillExtractionRequest, SkillExtractionResponse
from app.services.position_service import _load_with_skills


async def extract_skills_standalone(data: SkillExtractionRequest) -> SkillExtractionResponse:
    result = await skill_extraction_graph.ainvoke({
        "jd_text": data.jd_text,
        "position_id": None,
    })
    return SkillExtractionResponse(
        skills=result.get("skills", []),
        summary=result.get("summary", ""),
        suggested_seniority=result.get("suggested_seniority", "mid"),
        trace=result.get("trace", []),
    )


async def extract_and_apply_to_position(
    db: AsyncSession,
    position_id: uuid.UUID,
    data: SkillExtractionRequest,
) -> Position:
    position = await _load_with_skills(db, position_id)
    if not position:
        raise not_found("Position", str(position_id))

    # Snapshot existing skills into extraction history before overwriting
    skills_snapshot = [
        {
            "skill_name": s.skill_name,
            "category": s.category.value,
            "is_required": s.is_required,
            "min_proficiency": s.min_proficiency.value,
            "confidence": s.confidence.value,
            "source": s.source,
        }
        for s in position.required_skills
    ]

    result = await skill_extraction_graph.ainvoke({
        "jd_text": data.jd_text,
        "position_id": position_id,
    })

    db.add(ExtractionHistory(
        position_id=position_id,
        skills_snapshot=skills_snapshot,
        agent_trace=result.get("trace", []),
    ))

    # Replace position skills with extracted ones
    await db.execute(delete(PositionSkill).where(PositionSkill.position_id == position_id))
    await db.flush()

    for skill in result.get("skills", []):
        db.add(PositionSkill(
            position_id=position_id,
            skill_name=skill["skill_name"],
            category=skill["category"],
            is_required=skill["is_required"],
            min_proficiency=skill["min_proficiency"],
            confidence=skill["confidence"],
            source="ai_extracted",
        ))

    # Update AI summary fields
    position.ai_summary = result.get("summary")
    position.ai_seniority_suggestion = result.get("suggested_seniority")

    await db.commit()
    return await _load_with_skills(db, position_id)
