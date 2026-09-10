import re
import time
import uuid
from typing import Any, TypedDict

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from langgraph.graph import END, START, StateGraph

from app.agents.base import NodeLog, NodeLogger, get_trace
from app.core.llm import call_claude
from app.models.db import Candidate, Position
from app.services.scoring import score_candidate

node_logger = NodeLogger("MatchRecommendationGraph")

# ---------------------------------------------------------------------------
# Seniority fit
# ---------------------------------------------------------------------------

SENIORITY_YOE: dict[str, tuple[int, int]] = {
    "junior":    (0, 2),
    "mid":       (2, 5),
    "senior":    (5, 9),
    "lead":      (8, 13),
    "principal": (12, 99),
}


def seniority_multiplier(years: int, seniority: str) -> float:
    lo, hi = SENIORITY_YOE.get(seniority, (0, 99))
    if lo <= years <= hi:
        return 1.0
    gap = min(abs(years - lo), abs(years - hi))
    if gap <= 2:
        return 0.95
    return 0.85


def seniority_fits(years: int, seniority: str) -> bool:
    lo, hi = SENIORITY_YOE.get(seniority, (0, 99))
    return lo <= years <= hi


# ---------------------------------------------------------------------------
# Verdict
# ---------------------------------------------------------------------------

def compute_verdict(score: float, years: int, seniority: str) -> str:
    fits = seniority_fits(years, seniority)
    if score >= 85 and fits:
        return "Strong Match"
    if score >= 60 or (score >= 85 and not fits):
        return "Moderate Match"
    if score >= 40:
        return "Weak Match"
    return "Not Suitable"


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

RATIONALE_SYSTEM_PROMPT = """You are a technical recruiter AI. You will receive a position's requirements \
and a list of candidates with their skill profiles and match scores. \
For each candidate, write a concise, honest rationale (3-4 sentences) explaining \
why they are or are not a strong match. Be specific about matched and missing skills.

Format your response exactly as:
CANDIDATE_1: <rationale>
CANDIDATE_2: <rationale>
...

Do not include any other text outside these labeled blocks."""


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class MatchState(TypedDict, total=False):
    position_id: uuid.UUID
    db: Any                          # AsyncSession — passed through, not serialised
    top_n: int
    position_skills: list[dict]
    position_seniority: str
    position_title: str
    all_candidates: list[dict]
    scored_candidates: list[dict]
    ranked_candidates: list[dict]
    recommendations: list[dict]
    trace: list[NodeLog]


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

async def load_position_skills(state: MatchState) -> MatchState:
    t = time.perf_counter()
    db = state["db"]
    position_id = state["position_id"]

    result = await db.execute(
        select(Position)
        .options(selectinload(Position.required_skills))
        .where(Position.id == position_id)
    )
    position = result.scalar_one_or_none()

    if not position:
        entry = node_logger.log("load_position_skills", str(position_id), "position not found", t)
        return {**state, "position_skills": [], "trace": get_trace(state) + [entry]}

    skills = [
        {
            "skill_name": s.skill_name,
            "min_proficiency": s.min_proficiency.value,
            "is_required": s.is_required,
            "category": s.category.value,
        }
        for s in position.required_skills
    ]

    candidates_result = await db.execute(
        select(Candidate).options(selectinload(Candidate.skills))
    )
    candidates = candidates_result.scalars().all()

    all_candidates = [
        {
            "id": str(c.id),
            "full_name": c.full_name,
            "years_of_experience": c.years_of_experience,
            "current_role_title": c.current_role_title,
            "skills": [
                {"skill_name": s.skill_name, "proficiency": s.proficiency.value}
                for s in c.skills
            ],
        }
        for c in candidates
    ]

    entry = node_logger.log(
        "load_position_skills",
        str(position_id),
        f"{len(skills)} skills, {len(all_candidates)} candidates",
        t,
    )
    return {
        **state,
        "position_skills": skills,
        "position_seniority": position.seniority.value,
        "position_title": position.title,
        "all_candidates": all_candidates,
        "trace": get_trace(state) + [entry],
    }


async def score_all_candidates(state: MatchState) -> MatchState:
    t = time.perf_counter()
    position_skills = state["position_skills"]
    candidates = state.get("all_candidates", [])

    scored = []
    for candidate in candidates:
        result = score_candidate(candidate["skills"], position_skills)
        scored.append({
            **candidate,
            "base_score": result.base_score,
            "proficiency_bonus": result.proficiency_bonus,
            "preferred_bonus": result.preferred_bonus,
            "raw_score": result.final_score,
            "adjusted_score": result.final_score,
            "matched_skills": [s["skill_name"] for s in result.matched_skills],
            "partial_skills": [s["skill_name"] for s in result.partial_skills],
            "missing_skills": [s["skill_name"] for s in result.missing_skills],
        })

    entry = node_logger.log("score_all_candidates", f"{len(candidates)} candidates", f"scored all", t)
    return {**state, "scored_candidates": scored, "trace": get_trace(state) + [entry]}


async def apply_seniority_filter(state: MatchState) -> MatchState:
    t = time.perf_counter()
    seniority = state.get("position_seniority", "mid")
    scored = state.get("scored_candidates", [])

    adjusted = []
    for c in scored:
        multiplier = seniority_multiplier(c["years_of_experience"], seniority)
        adjusted.append({**c, "adjusted_score": round(c["raw_score"] * multiplier, 2)})

    entry = node_logger.log("apply_seniority_filter", f"seniority={seniority}", f"{len(adjusted)} adjusted", t)
    return {**state, "scored_candidates": adjusted, "trace": get_trace(state) + [entry]}


async def rank_candidates(state: MatchState) -> MatchState:
    t = time.perf_counter()
    top_n = state.get("top_n", 5)
    scored = state.get("scored_candidates", [])

    ranked = sorted(scored, key=lambda c: c["adjusted_score"], reverse=True)[:top_n]

    entry = node_logger.log("rank_candidates", f"top_n={top_n}", f"{len(ranked)} ranked", t)
    return {**state, "ranked_candidates": ranked, "trace": get_trace(state) + [entry]}


async def generate_rationales(state: MatchState) -> MatchState:
    t = time.perf_counter()
    ranked = state.get("ranked_candidates", [])
    position_title = state.get("position_title", "")
    position_skills = state.get("position_skills", [])

    if not ranked:
        entry = node_logger.log("generate_rationales", "no candidates", "skipped", t)
        return {**state, "trace": get_trace(state) + [entry]}

    required_names = [s["skill_name"] for s in position_skills if s["is_required"]]
    preferred_names = [s["skill_name"] for s in position_skills if not s["is_required"]]

    candidates_text = ""
    for i, c in enumerate(ranked, 1):
        candidates_text += (
            f"CANDIDATE_{i}: {c['full_name']} ({c['years_of_experience']} yrs exp, {c['current_role_title']})\n"
            f"  Skills: {', '.join(s['skill_name'] for s in c['skills'])}\n"
            f"  Score: {c['adjusted_score']:.1f}/100\n"
            f"  Matched: {', '.join(c['matched_skills']) or 'none'}\n"
            f"  Missing: {', '.join(c['missing_skills']) or 'none'}\n\n"
        )

    user_message = (
        f"Position: {position_title}\n"
        f"Required skills: {', '.join(required_names)}\n"
        f"Preferred skills: {', '.join(preferred_names)}\n\n"
        f"{candidates_text}"
        f"Write a rationale for each candidate."
    )

    raw, usage = await call_claude(
        system=RATIONALE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
        max_tokens=1024,
    )

    # Parse rationales by label
    rationale_map: dict[int, str] = {}
    for i in range(1, len(ranked) + 1):
        pattern = rf"CANDIDATE_{i}:\s*(.*?)(?=CANDIDATE_{i+1}:|$)"
        match = re.search(pattern, raw, re.DOTALL)
        rationale_map[i] = match.group(1).strip() if match else "Rationale unavailable."

    updated_ranked = []
    for i, c in enumerate(ranked, 1):
        updated_ranked.append({**c, "rationale": rationale_map.get(i, "Rationale unavailable.")})

    entry = node_logger.log(
        "generate_rationales",
        f"{len(ranked)} candidates",
        f"1 batched call, cache_read={usage['cache_read_input_tokens']}",
        t,
    )
    return {**state, "ranked_candidates": updated_ranked, "trace": get_trace(state) + [entry]}


async def compile_report(state: MatchState) -> MatchState:
    t = time.perf_counter()
    ranked = state.get("ranked_candidates", [])
    seniority = state.get("position_seniority", "mid")
    position_id = state["position_id"]

    recommendations = []
    for c in ranked:
        score = c["adjusted_score"]
        verdict = compute_verdict(score, c["years_of_experience"], seniority)
        recommendations.append({
            "position_id": str(position_id),
            "candidate_id": c["id"],
            "candidate_name": c["full_name"],
            "match_score": score,
            "matched_skills": c["matched_skills"],
            "missing_skills": c["missing_skills"],
            "partial_skills": c["partial_skills"],
            "rationale": c.get("rationale", ""),
            "suitability_verdict": verdict,
        })

    entry = node_logger.log("compile_report", f"{len(ranked)} ranked", f"{len(recommendations)} recommendations", t)
    return {**state, "recommendations": recommendations, "trace": get_trace(state) + [entry]}


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------

def build_match_recommendation_graph() -> StateGraph:
    graph = StateGraph(MatchState)

    graph.add_node("load_position_skills", load_position_skills)
    graph.add_node("score_all_candidates", score_all_candidates)
    graph.add_node("apply_seniority_filter", apply_seniority_filter)
    graph.add_node("rank_candidates", rank_candidates)
    graph.add_node("generate_rationales", generate_rationales)
    graph.add_node("compile_report", compile_report)

    graph.add_edge(START, "load_position_skills")
    graph.add_edge("load_position_skills", "score_all_candidates")
    graph.add_edge("score_all_candidates", "apply_seniority_filter")
    graph.add_edge("apply_seniority_filter", "rank_candidates")
    graph.add_edge("rank_candidates", "generate_rationales")
    graph.add_edge("generate_rationales", "compile_report")
    graph.add_edge("compile_report", END)

    return graph.compile()


match_recommendation_graph = build_match_recommendation_graph()
