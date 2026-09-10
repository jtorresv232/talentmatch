import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.api import BatchGapAnalysisResponse, GapAnalysisRequest, GapAnalysisResponse
from app.services import gap_analysis_service

router = APIRouter(tags=["gap-analysis"])


@router.post("/gap-analysis", response_model=GapAnalysisResponse)
async def gap_analysis(data: GapAnalysisRequest, db: AsyncSession = Depends(get_db)):
    return await gap_analysis_service.run_gap_analysis(db, data)


@router.post(
    "/positions/{position_id}/batch-gap-analysis",
    response_model=BatchGapAnalysisResponse,
)
async def batch_gap_analysis(
    position_id: uuid.UUID,
    top_n: int = Query(default=5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    return await gap_analysis_service.batch_gap_analysis(db, position_id, top_n)
