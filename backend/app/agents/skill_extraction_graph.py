import json
import re
import time
import uuid
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, ValidationError

from app.agents.base import NodeLog, NodeLogger, get_trace
from app.core.llm import call_claude

node_logger = NodeLogger("SkillExtractionGraph")

# ---------------------------------------------------------------------------
# Skill category classification lookup
# ---------------------------------------------------------------------------

SKILL_CATEGORY_MAP: dict[str, str] = {
    # Frontend
    "react": "frontend", "angular": "frontend", "vue": "frontend", "svelte": "frontend",
    "javascript": "frontend", "typescript": "frontend", "html": "frontend", "css": "frontend",
    "sass": "frontend", "tailwind": "frontend", "next.js": "frontend", "nuxt": "frontend",
    "redux": "frontend", "rxjs": "frontend", "webpack": "frontend", "vite": "frontend",
    "jest": "testing", "react testing library": "testing", "cypress": "testing",
    # Backend
    "node.js": "backend", "express": "backend", "fastapi": "backend", "django": "backend",
    "flask": "backend", ".net": "backend", "c#": "backend", "java": "backend",
    "spring boot": "backend", "spring": "backend", "python": "backend", "go": "backend",
    "rust": "backend", "ruby": "backend", "rails": "backend", "graphql": "backend",
    "rest api": "backend", "grpc": "backend", "kafka": "backend", "rabbitmq": "backend",
    # Database
    "postgresql": "database", "mysql": "database", "sql server": "database",
    "mongodb": "database", "redis": "database", "elasticsearch": "database",
    "sqlite": "database", "oracle": "database", "dynamodb": "database",
    "sql": "database",
    # Cloud
    "aws": "cloud", "azure": "cloud", "gcp": "cloud", "google cloud": "cloud",
    "s3": "cloud", "ec2": "cloud", "lambda": "cloud", "cloudformation": "cloud",
    # DevOps
    "docker": "devops", "kubernetes": "devops", "terraform": "devops", "ansible": "devops",
    "jenkins": "devops", "github actions": "devops", "gitlab ci": "devops", "ci/cd": "devops",
    "linux": "devops", "bash": "devops", "helm": "devops",
    # Mobile
    "react native": "mobile", "flutter": "mobile", "swift": "mobile", "kotlin": "mobile",
    "android": "mobile", "ios": "mobile",
    # Testing
    "pytest": "testing", "junit": "testing", "selenium": "testing", "playwright": "testing",
    "postman": "testing",
    # Architecture
    "microservices": "architecture", "system design": "architecture", "ddd": "architecture",
    "clean architecture": "architecture", "event sourcing": "architecture",
    # Soft skills
    "communication": "soft_skill", "leadership": "soft_skill", "mentoring": "soft_skill",
    "agile": "soft_skill", "scrum": "soft_skill",
}


def classify_category(skill_name: str) -> str:
    key = skill_name.lower().strip()
    return SKILL_CATEGORY_MAP.get(key, "other")


# ---------------------------------------------------------------------------
# Pydantic model for validating Claude's JSON output
# ---------------------------------------------------------------------------

VALID_CATEGORIES = {
    "frontend", "backend", "cloud", "devops", "database",
    "mobile", "testing", "architecture", "soft_skill", "other",
}
VALID_PROFICIENCIES = {"beginner", "intermediate", "advanced", "expert"}
VALID_CONFIDENCES = {"high", "medium", "low"}


class ExtractedSkillItem(BaseModel):
    skill_name: str
    category: str
    is_required: bool
    min_proficiency: str
    confidence: str

    def model_post_init(self, __context):
        if self.category not in VALID_CATEGORIES:
            raise ValueError(f"Invalid category: {self.category}")
        if self.min_proficiency not in VALID_PROFICIENCIES:
            raise ValueError(f"Invalid proficiency: {self.min_proficiency}")
        if self.confidence not in VALID_CONFIDENCES:
            raise ValueError(f"Invalid confidence: {self.confidence}")


class ClaudeExtractionOutput(BaseModel):
    skills: list[ExtractedSkillItem]
    role_summary: str
    suggested_seniority: str


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class ExtractionState(TypedDict, total=False):
    # Inputs
    jd_text: str
    position_id: uuid.UUID | None

    # Intermediate
    cleaned_text: str
    raw_claude_output: str
    retry_count: int
    is_valid: bool
    validation_error: str | None
    parsed_output: dict

    # Outputs
    skills: list[dict]
    summary: str
    suggested_seniority: str
    trace: list[NodeLog]
    error: str | None


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

EXTRACTION_SYSTEM_PROMPT = """You are a technical recruiter assistant specializing in software engineering roles.
Your task is to extract structured skill requirements from job descriptions.

Always return valid JSON matching this schema:
{
  "skills": [
    {
      "skill_name": "string",
      "category": "frontend|backend|cloud|devops|database|mobile|testing|architecture|soft_skill|other",
      "is_required": true|false,
      "min_proficiency": "beginner|intermediate|advanced|expert",
      "confidence": "high|medium|low"
    }
  ],
  "role_summary": "string (2-3 sentences)",
  "suggested_seniority": "junior|mid|senior|lead|principal"
}

Rules:
- Only include skills explicitly stated or strongly implied by the JD.
- Do not invent skills not present in the text.
- Prefer specific technologies over vague terms (e.g., "React" not "JavaScript framework").
- Mark as required only what the JD explicitly marks as required or essential.
- Return ONLY the JSON object, no markdown fences or extra text."""

SUMMARY_SYSTEM_PROMPT = """You are a technical recruiter assistant.
Given a job description, write a concise role summary (2-3 sentences) and suggest the seniority level.
Return ONLY valid JSON: {"role_summary": "...", "suggested_seniority": "junior|mid|senior|lead|principal"}"""


# ---------------------------------------------------------------------------
# Node helpers
# ---------------------------------------------------------------------------

def _extract_json(text: str) -> str:
    """Strip markdown code fences if Claude wraps the JSON."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        return match.group(1).strip()
    return text


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

async def parse_jd(state: ExtractionState) -> ExtractionState:
    t = time.perf_counter()
    jd = state["jd_text"]

    # Normalise whitespace and strip boilerplate noise
    cleaned = re.sub(r"\s+", " ", jd).strip()
    cleaned = re.sub(r"(Equal Opportunity Employer.*)", "", cleaned, flags=re.IGNORECASE)

    entry = node_logger.log("parse_jd", f"{len(jd)} chars", f"{len(cleaned)} chars cleaned", t)
    return {
        **state,
        "cleaned_text": cleaned,
        "retry_count": 0,
        "trace": get_trace(state) + [entry],
    }


async def extract_skills(state: ExtractionState) -> ExtractionState:
    t = time.perf_counter()
    retry = state.get("retry_count", 0)
    text = state["cleaned_text"]

    user_content = f"Extract skills from this job description:\n\n{text}"

    if retry > 0:
        error = state.get("validation_error", "")
        user_content += (
            f"\n\nYour previous response was invalid. Error: {error}\n"
            "Please fix the JSON and try again. Return ONLY valid JSON."
        )

    raw, usage = await call_claude(
        system=EXTRACTION_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
        max_tokens=2048,
    )

    entry = node_logger.log(
        "extract_skills",
        f"retry={retry}, {len(text)} chars",
        f"raw output {len(raw)} chars, cache_read={usage['cache_read_input_tokens']}",
        t,
    )
    return {
        **state,
        "raw_claude_output": raw,
        "trace": get_trace(state) + [entry],
    }


async def validate_schema(state: ExtractionState) -> ExtractionState:
    t = time.perf_counter()
    raw = state["raw_claude_output"]
    retry = state.get("retry_count", 0)

    try:
        json_str = _extract_json(raw)
        data = json.loads(json_str)
        ClaudeExtractionOutput(**data)
        entry = node_logger.log("validate_schema", f"retry={retry}", "valid", t)
        return {
            **state,
            "is_valid": True,
            "parsed_output": data,
            "validation_error": None,
            "trace": get_trace(state) + [entry],
        }
    except (json.JSONDecodeError, ValidationError, Exception) as e:
        entry = node_logger.log("validate_schema", f"retry={retry}", f"invalid: {e}", t)
        return {
            **state,
            "is_valid": False,
            "retry_count": retry + 1,
            "validation_error": str(e),
            "trace": get_trace(state) + [entry],
        }


def should_retry(state: ExtractionState) -> str:
    if not state.get("is_valid") and state.get("retry_count", 0) < 2:
        return "extract_skills"
    return "classify_skills"


async def classify_skills(state: ExtractionState) -> ExtractionState:
    t = time.perf_counter()
    parsed = state.get("parsed_output", {})
    raw_skills = parsed.get("skills", [])

    classified = []
    for skill in raw_skills:
        inferred_category = classify_category(skill["skill_name"])
        # Use Claude's category if it's specific, fallback to rule-based if Claude said "other"
        final_category = skill["category"] if skill["category"] != "other" else inferred_category
        classified.append({**skill, "category": final_category})

    entry = node_logger.log("classify_skills", f"{len(raw_skills)} skills", f"{len(classified)} classified", t)
    return {
        **state,
        "skills": classified,
        "trace": get_trace(state) + [entry],
    }


async def generate_summary(state: ExtractionState) -> ExtractionState:
    t = time.perf_counter()

    # Re-use summary from Claude's extraction output if valid
    parsed = state.get("parsed_output", {})
    summary = parsed.get("role_summary", "")
    seniority = parsed.get("suggested_seniority", "mid")

    if not summary:
        raw, _ = await call_claude(
            system=SUMMARY_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": state["cleaned_text"]}],
            max_tokens=512,
        )
        try:
            data = json.loads(_extract_json(raw))
            summary = data.get("role_summary", "")
            seniority = data.get("suggested_seniority", "mid")
        except Exception:
            summary = "Role summary unavailable."
            seniority = "mid"

    entry = node_logger.log("generate_summary", "extracted output", f"seniority={seniority}", t)
    return {
        **state,
        "summary": summary,
        "suggested_seniority": seniority,
        "trace": get_trace(state) + [entry],
    }


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------

def build_skill_extraction_graph() -> StateGraph:
    graph = StateGraph(ExtractionState)

    graph.add_node("parse_jd", parse_jd)
    graph.add_node("extract_skills", extract_skills)
    graph.add_node("validate_schema", validate_schema)
    graph.add_node("classify_skills", classify_skills)
    graph.add_node("generate_summary", generate_summary)

    graph.add_edge(START, "parse_jd")
    graph.add_edge("parse_jd", "extract_skills")
    graph.add_edge("extract_skills", "validate_schema")
    graph.add_conditional_edges("validate_schema", should_retry, {
        "extract_skills": "extract_skills",
        "classify_skills": "classify_skills",
    })
    graph.add_edge("classify_skills", "generate_summary")
    graph.add_edge("generate_summary", END)

    return graph.compile()


skill_extraction_graph = build_skill_extraction_graph()
