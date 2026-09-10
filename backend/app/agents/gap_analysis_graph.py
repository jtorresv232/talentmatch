import time
import uuid
from typing import Any, TypedDict

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from langgraph.graph import END, START, StateGraph

from app.agents.base import NodeLog, NodeLogger, get_trace
from app.agents.match_recommendation_graph import SENIORITY_YOE, compute_verdict, seniority_fits
from app.core.llm import call_claude
from app.models.db import Candidate, Position
from app.services.scoring import PROFICIENCY_SCORE, score_candidate

node_logger = NodeLogger("GapAnalysisGraph")

# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

GAP_ANALYSIS_SYSTEM_PROMPT = """You are a technical career advisor. You will receive a structured \
skill gap analysis between a candidate and a position. For each missing or partial skill, provide \
a specific, actionable development recommendation.

Format each recommendation exactly as:
- Skill: [skill name]
  Gap: [what's missing — be specific about the proficiency level needed]
  Recommendation: [specific action with estimated timeframe]

Keep recommendations realistic and focused on software engineering growth paths.
Only output the bulleted list, nothing else."""

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class GapState(TypedDict, total=False):
    candidate_id: uuid.UUID
    position_id: uuid.UUID
    db: Any                   # AsyncSession

    # Loaded data
    candidate: dict
    position: dict

    # Diff results
    fully_matched: list[dict]
    partial: list[dict]
    missing: list[dict]

    # Seniority assessment
    seniority_fit: bool
    seniority_note: str

    # Scoring
    score: float

    # AI output
    recommendations: list[str]

    # Final
    verdict: str
    trace: list[NodeLog]


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

async def load_pair(state: GapState) -> GapState:
    t = time.perf_counter()
    db = state["db"]

    candidate_result = await db.execute(
        select(Candidate)
        .options(selectinload(Candidate.skills))
        .where(Candidate.id == state["candidate_id"])
    )
    candidate = candidate_result.scalar_one_or_none()

    position_result = await db.execute(
        select(Position)
        .options(selectinload(Position.required_skills))
        .where(Position.id == state["position_id"])
    )
    position = position_result.scalar_one_or_none()

    candidate_dict = {
        "id": str(candidate.id),
        "full_name": candidate.full_name,
        "years_of_experience": candidate.years_of_experience,
        "current_role_title": candidate.current_role_title,
        "skills": [
            {"skill_name": s.skill_name, "proficiency": s.proficiency.value, "category": s.category.value}
            for s in candidate.skills
        ],
    } if candidate else {}

    position_dict = {
        "id": str(position.id),
        "title": position.title,
        "seniority": position.seniority.value,
        "required_skills": [
            {
                "skill_name": s.skill_name,
                "min_proficiency": s.min_proficiency.value,
                "is_required": s.is_required,
                "category": s.category.value,
            }
            for s in position.required_skills
        ],
    } if position else {}

    entry = node_logger.log(
        "load_pair",
        f"candidate={state['candidate_id']}, position={state['position_id']}",
        f"candidate={'found' if candidate else 'missing'}, position={'found' if position else 'missing'}",
        t,
    )
    return {**state, "candidate": candidate_dict, "position": position_dict, "trace": get_trace(state) + [entry]}


async def diff_skills(state: GapState) -> GapState:
    t = time.perf_counter()
    candidate = state.get("candidate", {})
    position = state.get("position", {})

    candidate_map = {
        s["skill_name"].lower(): s
        for s in candidate.get("skills", [])
    }

    fully_matched: list[dict] = []
    partial: list[dict] = []
    missing: list[dict] = []

    for req in position.get("required_skills", []):
        name = req["skill_name"].lower()
        required_score = PROFICIENCY_SCORE[req["min_proficiency"]]
        candidate_skill = candidate_map.get(name)

        if candidate_skill is None:
            missing.append(req)
        elif PROFICIENCY_SCORE[candidate_skill["proficiency"]] >= required_score:
            fully_matched.append({
                **req,
                "candidate_proficiency": candidate_skill["proficiency"],
            })
        else:
            partial.append({
                **req,
                "candidate_proficiency": candidate_skill["proficiency"],
            })

    # Use scoring engine for the numeric score
    candidate_skills_list = [
        {"skill_name": s["skill_name"], "proficiency": s["proficiency"]}
        for s in candidate.get("skills", [])
    ]
    scoring = score_candidate(candidate_skills_list, position.get("required_skills", []))

    entry = node_logger.log(
        "diff_skills",
        f"{len(position.get('required_skills', []))} required skills",
        f"matched={len(fully_matched)}, partial={len(partial)}, missing={len(missing)}",
        t,
    )
    return {
        **state,
        "fully_matched": fully_matched,
        "partial": partial,
        "missing": missing,
        "score": scoring.final_score,
        "trace": get_trace(state) + [entry],
    }


async def assess_seniority_fit(state: GapState) -> GapState:
    t = time.perf_counter()
    years = state.get("candidate", {}).get("years_of_experience", 0)
    seniority = state.get("position", {}).get("seniority", "mid")

    fits = seniority_fits(years, seniority)
    lo, hi = SENIORITY_YOE.get(seniority, (0, 99))

    if fits:
        note = f"Candidate's {years} years of experience fits the {seniority} level ({lo}–{hi} yrs expected)."
    elif years < lo:
        note = f"Candidate has {years} years; {seniority} typically requires {lo}+ years."
    else:
        note = f"Candidate is overqualified at {years} years; {seniority} typically caps at {hi} years."

    entry = node_logger.log("assess_seniority_fit", f"years={years}, seniority={seniority}", note, t)
    return {**state, "seniority_fit": fits, "seniority_note": note, "trace": get_trace(state) + [entry]}


async def generate_gap_report(state: GapState) -> GapState:
    t = time.perf_counter()
    partial = state.get("partial", [])
    missing = state.get("missing", [])
    gaps = partial + missing

    if not gaps:
        entry = node_logger.log("generate_gap_report", "no gaps", "skipped", t)
        return {**state, "recommendations": [], "trace": get_trace(state) + [entry]}

    candidate = state.get("candidate", {})
    position = state.get("position", {})

    gaps_text = ""
    for g in partial:
        gaps_text += (
            f"- {g['skill_name']}: candidate has {g.get('candidate_proficiency', '?')}, "
            f"needs {g['min_proficiency']} (partial gap)\n"
        )
    for g in missing:
        gaps_text += f"- {g['skill_name']}: completely missing, needs {g['min_proficiency']}\n"

    user_message = (
        f"Candidate: {candidate.get('full_name')} ({candidate.get('years_of_experience')} yrs, "
        f"{candidate.get('current_role_title')})\n"
        f"Position: {position.get('title')} ({position.get('seniority')})\n\n"
        f"Skill gaps:\n{gaps_text}"
    )

    raw, usage = await call_claude(
        system=GAP_ANALYSIS_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
        max_tokens=1024,
    )

    # Split into individual recommendations by "- Skill:" blocks
    recommendations = [
        block.strip()
        for block in raw.split("- Skill:")
        if block.strip()
    ]
    recommendations = [f"- Skill: {r}" for r in recommendations]

    entry = node_logger.log(
        "generate_gap_report",
        f"{len(gaps)} gaps",
        f"{len(recommendations)} recommendations, cache_read={usage['cache_read_input_tokens']}",
        t,
    )
    return {**state, "recommendations": recommendations, "trace": get_trace(state) + [entry]}


async def produce_verdict(state: GapState) -> GapState:
    t = time.perf_counter()
    score = state.get("score", 0.0)
    years = state.get("candidate", {}).get("years_of_experience", 0)
    seniority = state.get("position", {}).get("seniority", "mid")

    verdict = compute_verdict(score, years, seniority)

    entry = node_logger.log("produce_verdict", f"score={score:.1f}", f"verdict={verdict}", t)
    return {**state, "verdict": verdict, "trace": get_trace(state) + [entry]}


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------

def build_gap_analysis_graph() -> StateGraph:
    graph = StateGraph(GapState)

    graph.add_node("load_pair", load_pair)
    graph.add_node("diff_skills", diff_skills)
    graph.add_node("assess_seniority_fit", assess_seniority_fit)
    graph.add_node("generate_gap_report", generate_gap_report)
    graph.add_node("produce_verdict", produce_verdict)

    graph.add_edge(START, "load_pair")
    graph.add_edge("load_pair", "diff_skills")
    graph.add_edge("diff_skills", "assess_seniority_fit")
    graph.add_edge("assess_seniority_fit", "generate_gap_report")
    graph.add_edge("generate_gap_report", "produce_verdict")
    graph.add_edge("produce_verdict", END)

    return graph.compile()


gap_analysis_graph = build_gap_analysis_graph()
