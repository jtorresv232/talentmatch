import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.api import CandidateRecommendationRead, PositionRecommendationRead
from app.services import recommendation_service

router = APIRouter(tags=["recommendations"])


@router.post(
    "/positions/{position_id}/recommend-candidates",
    response_model=list[CandidateRecommendationRead],
)
async def recommend_candidates(
    position_id: uuid.UUID,
    top_n: int = Query(default=5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    return await recommendation_service.recommend_candidates(db, position_id, top_n)


@router.post(
    "/candidates/{candidate_id}/recommend-positions",
    response_model=list[PositionRecommendationRead],
)
async def recommend_positions(
    candidate_id: uuid.UUID,
    top_n: int = Query(default=5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    return await recommendation_service.recommend_positions(db, candidate_id, top_n)
