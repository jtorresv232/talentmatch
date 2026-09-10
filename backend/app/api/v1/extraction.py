import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.api import PositionRead, SkillExtractionRequest, SkillExtractionResponse
from app.services import agent_service

router = APIRouter(tags=["skill-extraction"])


@router.post("/extract-skills", response_model=SkillExtractionResponse)
async def extract_skills(data: SkillExtractionRequest):
    return await agent_service.extract_skills_standalone(data)


@router.post("/positions/{position_id}/extract-skills", response_model=PositionRead)
async def extract_and_apply(
    position_id: uuid.UUID,
    data: SkillExtractionRequest,
    db: AsyncSession = Depends(get_db),
):
    return await agent_service.extract_and_apply_to_position(db, position_id, data)
