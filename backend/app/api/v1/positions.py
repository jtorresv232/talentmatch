import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.api import PositionCreate, PositionListRead, PositionRead, PositionUpdate
from app.services import position_service

router = APIRouter(prefix="/positions", tags=["positions"])


@router.post("", response_model=PositionRead, status_code=status.HTTP_201_CREATED)
async def create_position(data: PositionCreate, db: AsyncSession = Depends(get_db)):
    return await position_service.create_position(db, data)


@router.get("", response_model=list[PositionListRead])
async def list_positions(
    status: str | None = None,
    seniority: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await position_service.list_positions(db, status, seniority)


@router.get("/{position_id}", response_model=PositionRead)
async def get_position(position_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await position_service.get_position(db, position_id)


@router.patch("/{position_id}", response_model=PositionRead)
async def update_position(
    position_id: uuid.UUID,
    data: PositionUpdate,
    db: AsyncSession = Depends(get_db),
):
    return await position_service.update_position(db, position_id, data)
