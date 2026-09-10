import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.api import CandidateCreate, CandidateListRead, CandidateRead, CandidateUpdate
from app.services import candidate_service

router = APIRouter(prefix="/candidates", tags=["candidates"])


@router.post("", response_model=CandidateRead, status_code=status.HTTP_201_CREATED)
async def create_candidate(data: CandidateCreate, db: AsyncSession = Depends(get_db)):
    return await candidate_service.create_candidate(db, data)


@router.get("", response_model=list[CandidateListRead])
async def list_candidates(
    skill_name: str | None = None,
    category: str | None = None,
    min_proficiency: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await candidate_service.list_candidates(db, skill_name, category, min_proficiency)


@router.get("/{candidate_id}", response_model=CandidateRead)
async def get_candidate(candidate_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await candidate_service.get_candidate(db, candidate_id)


@router.patch("/{candidate_id}", response_model=CandidateRead)
async def update_candidate(
    candidate_id: uuid.UUID,
    data: CandidateUpdate,
    db: AsyncSession = Depends(get_db),
):
    return await candidate_service.update_candidate(db, candidate_id, data)


@router.delete("/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_candidate(candidate_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    await candidate_service.delete_candidate(db, candidate_id)
