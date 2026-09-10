import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.gap_analysis_graph import gap_analysis_graph
from app.core.errors import not_found
from app.models.db import Candidate, Position
from app.schemas.api import (
    BatchGapAnalysisResponse,
    GapAnalysisRequest,
    GapAnalysisResponse,
    SkillGapItem,
)
from app.services.scoring import score_candidate


async def run_gap_analysis(
    db: AsyncSession,
    data: GapAnalysisRequest,
) -> GapAnalysisResponse:
    candidate = await db.get(Candidate, data.candidate_id)
    if not candidate:
        raise not_found("Candidate", str(data.candidate_id))

    position = await db.get(Position, data.position_id)
    if not position:
        raise not_found("Position", str(data.position_id))

    state = await gap_analysis_graph.ainvoke({
        "candidate_id": data.candidate_id,
        "position_id": data.position_id,
        "db": db,
    })

    return _build_response(state)


async def batch_gap_analysis(
    db: AsyncSession,
    position_id: uuid.UUID,
    top_n: int = 5,
) -> BatchGapAnalysisResponse:
    position_result = await db.execute(
        select(Position)
        .options(selectinload(Position.required_skills))
        .where(Position.id == position_id)
    )
    position = position_result.scalar_one_or_none()
    if not position:
        raise not_found("Position", str(position_id))

    candidates_result = await db.execute(
        select(Candidate).options(selectinload(Candidate.skills))
    )
    candidates = candidates_result.scalars().all()

    position_skills = [
        {"skill_name": s.skill_name, "min_proficiency": s.min_proficiency.value, "is_required": s.is_required}
        for s in position.required_skills
    ]

    # Score and rank all candidates, take top N
    scored = []
    for candidate in candidates:
        candidate_skills = [
            {"skill_name": s.skill_name, "proficiency": s.proficiency.value}
            for s in candidate.skills
        ]
        result = score_candidate(candidate_skills, position_skills)
        scored.append((candidate, result.final_score))

    top_candidates = sorted(scored, key=lambda x: x[1], reverse=True)[:top_n]

    # Run gap analysis for each
    results = []
    for candidate, _ in top_candidates:
        state = await gap_analysis_graph.ainvoke({
            "candidate_id": candidate.id,
            "position_id": position_id,
            "db": db,
        })
        results.append(_build_response(state))

    return BatchGapAnalysisResponse(
        position_id=position_id,
        position_title=position.title,
        results=results,
    )


def _build_response(state: dict) -> GapAnalysisResponse:
    candidate = state.get("candidate", {})
    position = state.get("position", {})

    return GapAnalysisResponse(
        candidate_id=uuid.UUID(candidate["id"]),
        candidate_name=candidate.get("full_name", ""),
        position_id=uuid.UUID(position["id"]),
        position_title=position.get("title", ""),
        score=state.get("score", 0.0),
        verdict=state.get("verdict", "Not Suitable"),
        seniority_fit=state.get("seniority_fit", False),
        seniority_note=state.get("seniority_note", ""),
        fully_matched=[SkillGapItem(**s) for s in state.get("fully_matched", [])],
        partial=[SkillGapItem(**s) for s in state.get("partial", [])],
        missing=[SkillGapItem(**s) for s in state.get("missing", [])],
        recommendations=state.get("recommendations", []),
        trace=state.get("trace", []),
    )
