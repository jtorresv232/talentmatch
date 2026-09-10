import uuid

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import AppError, not_found
from app.models.db import Candidate, CandidateSkill, Proficiency, PROFICIENCY_ORDER
from app.schemas.api import CandidateCreate, CandidateUpdate


async def create_candidate(db: AsyncSession, data: CandidateCreate) -> Candidate:
    candidate = Candidate(
        full_name=data.full_name,
        email=data.email,
        years_of_experience=data.years_of_experience,
        current_role_title=data.current_role_title,
        summary=data.summary,
    )
    db.add(candidate)
    await db.flush()

    for skill_data in data.skills:
        db.add(CandidateSkill(
            candidate_id=candidate.id,
            skill_name=skill_data.skill_name,
            category=skill_data.category,
            proficiency=skill_data.proficiency,
            years_used=skill_data.years_used,
        ))

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise AppError(detail="A candidate with this email already exists.", code="email_conflict", status_code=409)
    return await _load_with_skills(db, candidate.id)


async def get_candidate(db: AsyncSession, candidate_id: uuid.UUID) -> Candidate:
    candidate = await _load_with_skills(db, candidate_id)
    if not candidate:
        raise not_found("Candidate", str(candidate_id))
    return candidate


async def update_candidate(db: AsyncSession, candidate_id: uuid.UUID, data: CandidateUpdate) -> Candidate:
    candidate = await _load_with_skills(db, candidate_id)
    if not candidate:
        raise not_found("Candidate", str(candidate_id))

    if data.full_name is not None:
        candidate.full_name = data.full_name
    if data.email is not None:
        candidate.email = data.email
    if data.years_of_experience is not None:
        candidate.years_of_experience = data.years_of_experience
    if data.current_role_title is not None:
        candidate.current_role_title = data.current_role_title
    if data.summary is not None:
        candidate.summary = data.summary

    if data.skills is not None:
        await db.execute(delete(CandidateSkill).where(CandidateSkill.candidate_id == candidate_id))
        await db.flush()
        for skill_data in data.skills:
            db.add(CandidateSkill(
                candidate_id=candidate.id,
                skill_name=skill_data.skill_name,
                category=skill_data.category,
                proficiency=skill_data.proficiency,
                years_used=skill_data.years_used,
            ))

    await db.commit()
    return await _load_with_skills(db, candidate_id)


async def delete_candidate(db: AsyncSession, candidate_id: uuid.UUID) -> None:
    candidate = await db.get(Candidate, candidate_id)
    if not candidate:
        raise not_found("Candidate", str(candidate_id))
    await db.delete(candidate)
    await db.commit()


async def list_candidates(
    db: AsyncSession,
    skill_name: str | None = None,
    category: str | None = None,
    min_proficiency: str | None = None,
) -> list[Candidate]:
    stmt = (
        select(Candidate)
        .options(selectinload(Candidate.skills))
        .order_by(Candidate.created_at.desc())
    )

    if skill_name or category or min_proficiency:
        stmt = stmt.join(Candidate.skills)

        if skill_name:
            stmt = stmt.where(CandidateSkill.skill_name.ilike(f"%{skill_name}%"))

        if category:
            stmt = stmt.where(CandidateSkill.category == category)

        if min_proficiency:
            min_level = PROFICIENCY_ORDER[Proficiency(min_proficiency)]
            valid = [p.value for p, level in PROFICIENCY_ORDER.items() if level >= min_level]
            stmt = stmt.where(CandidateSkill.proficiency.in_(valid))

        stmt = stmt.distinct()

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def _load_with_skills(db: AsyncSession, candidate_id: uuid.UUID) -> Candidate | None:
    result = await db.execute(
        select(Candidate)
        .options(selectinload(Candidate.skills))
        .where(Candidate.id == candidate_id)
    )
    return result.scalar_one_or_none()
