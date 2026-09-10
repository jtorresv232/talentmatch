import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.match_recommendation_graph import (
    compute_verdict,
    match_recommendation_graph,
    seniority_multiplier,
)
from app.core.errors import not_found
from app.core.llm import call_claude
from app.agents.match_recommendation_graph import RATIONALE_SYSTEM_PROMPT
from app.models.db import Candidate, Position, RecommendationResult
from app.schemas.api import CandidateRecommendationRead, PositionRecommendationRead
from app.services.scoring import score_candidate


async def recommend_candidates(
    db: AsyncSession,
    position_id: uuid.UUID,
    top_n: int = 5,
) -> list[CandidateRecommendationRead]:
    result = await db.execute(
        select(Position).where(Position.id == position_id)
    )
    if not result.scalar_one_or_none():
        raise not_found("Position", str(position_id))

    state = await match_recommendation_graph.ainvoke({
        "position_id": position_id,
        "db": db,
        "top_n": top_n,
    })

    recommendations = state.get("recommendations", [])

    # Persist to DB
    for rec in recommendations:
        db.add(RecommendationResult(
            position_id=uuid.UUID(rec["position_id"]),
            candidate_id=uuid.UUID(rec["candidate_id"]),
            match_score=rec["match_score"],
            matched_skills=rec["matched_skills"],
            missing_skills=rec["missing_skills"],
            partial_skills=rec["partial_skills"],
            rationale=rec["rationale"],
            suitability_verdict=rec["suitability_verdict"],
        ))
    await db.commit()

    # Enrich with candidate details for response
    candidate_ids = [uuid.UUID(r["candidate_id"]) for r in recommendations]
    candidates_result = await db.execute(
        select(Candidate).where(Candidate.id.in_(candidate_ids))
    )
    candidate_map = {str(c.id): c for c in candidates_result.scalars().all()}

    output = []
    for rec in recommendations:
        candidate = candidate_map.get(rec["candidate_id"])
        output.append(CandidateRecommendationRead(
            candidate_id=uuid.UUID(rec["candidate_id"]),
            candidate_name=rec["candidate_name"],
            current_role_title=candidate.current_role_title if candidate else "",
            years_of_experience=candidate.years_of_experience if candidate else 0,
            match_score=rec["match_score"],
            matched_skills=rec["matched_skills"],
            missing_skills=rec["missing_skills"],
            partial_skills=rec["partial_skills"],
            rationale=rec["rationale"],
            suitability_verdict=rec["suitability_verdict"],
        ))
    return output


async def recommend_positions(
    db: AsyncSession,
    candidate_id: uuid.UUID,
    top_n: int = 5,
) -> list[PositionRecommendationRead]:
    candidate_result = await db.execute(
        select(Candidate)
        .options(selectinload(Candidate.skills))
        .where(Candidate.id == candidate_id)
    )
    candidate = candidate_result.scalar_one_or_none()
    if not candidate:
        raise not_found("Candidate", str(candidate_id))

    positions_result = await db.execute(
        select(Position).options(selectinload(Position.required_skills))
    )
    positions = positions_result.scalars().all()

    candidate_skills = [
        {"skill_name": s.skill_name, "proficiency": s.proficiency.value}
        for s in candidate.skills
    ]

    scored = []
    for position in positions:
        position_skills = [
            {
                "skill_name": s.skill_name,
                "min_proficiency": s.min_proficiency.value,
                "is_required": s.is_required,
            }
            for s in position.required_skills
        ]
        result = score_candidate(candidate_skills, position_skills)
        multiplier = seniority_multiplier(candidate.years_of_experience, position.seniority.value)
        adjusted = round(result.final_score * multiplier, 2)

        scored.append({
            "position": position,
            "adjusted_score": adjusted,
            "matched_skills": [s["skill_name"] for s in result.matched_skills],
            "missing_skills": [s["skill_name"] for s in result.missing_skills],
            "partial_skills": [s["skill_name"] for s in result.partial_skills],
        })

    ranked = sorted(scored, key=lambda x: x["adjusted_score"], reverse=True)[:top_n]

    if not ranked:
        return []

    # Batched rationale call
    positions_text = ""
    for i, item in enumerate(ranked, 1):
        pos = item["position"]
        positions_text += (
            f"CANDIDATE_{i}: {pos.title} ({pos.seniority.value}, {pos.department})\n"
            f"  Required: {', '.join(s.skill_name for s in pos.required_skills if s.is_required)}\n"
            f"  Score: {item['adjusted_score']:.1f}/100\n"
            f"  Matched: {', '.join(item['matched_skills']) or 'none'}\n"
            f"  Missing: {', '.join(item['missing_skills']) or 'none'}\n\n"
        )

    user_message = (
        f"Candidate: {candidate.full_name} ({candidate.years_of_experience} yrs, {candidate.current_role_title})\n"
        f"Skills: {', '.join(s.skill_name for s in candidate.skills)}\n\n"
        f"{positions_text}"
        f"Write a rationale for each position fit."
    )

    raw, _ = await call_claude(
        system=RATIONALE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
        max_tokens=1024,
    )

    import re
    output = []
    for i, item in enumerate(ranked, 1):
        pos = item["position"]
        pattern = rf"CANDIDATE_{i}:\s*(.*?)(?=CANDIDATE_{i+1}:|$)"
        match = re.search(pattern, raw, re.DOTALL)
        rationale = match.group(1).strip() if match else "Rationale unavailable."
        verdict = compute_verdict(
            item["adjusted_score"], candidate.years_of_experience, pos.seniority.value
        )
        output.append(PositionRecommendationRead(
            position_id=pos.id,
            position_title=pos.title,
            department=pos.department,
            seniority=pos.seniority.value,
            match_score=item["adjusted_score"],
            matched_skills=item["matched_skills"],
            missing_skills=item["missing_skills"],
            partial_skills=item["partial_skills"],
            rationale=rationale,
            suitability_verdict=verdict,
        ))
    return output
