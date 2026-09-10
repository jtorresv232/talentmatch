import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import not_found
from app.models.db import Position, PositionSkill
from app.schemas.api import PositionCreate, PositionUpdate


async def create_position(db: AsyncSession, data: PositionCreate) -> Position:
    position = Position(
        title=data.title,
        department=data.department,
        seniority=data.seniority,
        status=data.status,
        description_raw=data.description_raw,
    )
    db.add(position)
    await db.flush()

    for skill_data in data.required_skills:
        db.add(PositionSkill(
            position_id=position.id,
            skill_name=skill_data.skill_name,
            category=skill_data.category,
            is_required=skill_data.is_required,
            min_proficiency=skill_data.min_proficiency,
            confidence=skill_data.confidence,
            source=skill_data.source,
        ))

    await db.commit()
    return await _load_with_skills(db, position.id)


async def get_position(db: AsyncSession, position_id: uuid.UUID) -> Position:
    position = await _load_with_skills(db, position_id)
    if not position:
        raise not_found("Position", str(position_id))
    return position


async def update_position(db: AsyncSession, position_id: uuid.UUID, data: PositionUpdate) -> Position:
    position = await _load_with_skills(db, position_id)
    if not position:
        raise not_found("Position", str(position_id))

    if data.title is not None:
        position.title = data.title
    if data.department is not None:
        position.department = data.department
    if data.seniority is not None:
        position.seniority = data.seniority
    if data.status is not None:
        position.status = data.status
    if data.description_raw is not None:
        position.description_raw = data.description_raw

    if data.required_skills is not None:
        await db.execute(delete(PositionSkill).where(PositionSkill.position_id == position_id))
        await db.flush()
        for skill_data in data.required_skills:
            db.add(PositionSkill(
                position_id=position.id,
                skill_name=skill_data.skill_name,
                category=skill_data.category,
                is_required=skill_data.is_required,
                min_proficiency=skill_data.min_proficiency,
                confidence=skill_data.confidence,
                source=skill_data.source,
            ))

    await db.commit()
    return await _load_with_skills(db, position_id)


async def list_positions(
    db: AsyncSession,
    status: str | None = None,
    seniority: str | None = None,
) -> list[Position]:
    stmt = (
        select(Position)
        .options(selectinload(Position.required_skills))
        .order_by(Position.created_at.desc())
    )

    if status:
        stmt = stmt.where(Position.status == status)
    if seniority:
        stmt = stmt.where(Position.seniority == seniority)

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def _load_with_skills(db: AsyncSession, position_id: uuid.UUID) -> Position | None:
    result = await db.execute(
        select(Position)
        .options(selectinload(Position.required_skills))
        .where(Position.id == position_id)
    )
    return result.scalar_one_or_none()
