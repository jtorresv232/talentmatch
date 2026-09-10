# TalentMatch AI — Technical Specification

**Project:** AI-Powered Talent Intelligence Platform for Software Engineering Roles  
**Version:** 1.0  
**Date:** 2026-09-09

---

## 1. System Overview

TalentMatch AI is an agentic platform that helps companies manage a talent bank of software engineers and open engineering positions, and uses AI to extract skill requirements from job descriptions and recommend candidate-position matches.

The system is intentionally built around **agentic workflows** (LangGraph) rather than simple prompt calls, to demonstrate multi-step AI reasoning with structured state, retries, and observable node-by-node execution — consistent with the Perficient AI Platform architecture.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────┐
│                     React Frontend                  │
│              (Dashboard · Forms · Views)            │
└───────────────────────┬─────────────────────────────┘
                        │ HTTP / REST
┌───────────────────────▼─────────────────────────────┐
│               FastAPI Application Layer              │
│         (Routers · Schemas · Auth-ready)            │
├─────────────────────────────────────────────────────┤
│              Service Layer (Business Logic)          │
│   CandidateService · PositionService · AgentService │
├────────────────┬────────────────────────────────────┤
│  LangGraph     │         Data Access Layer           │
│  Agent Graphs  │       (SQLAlchemy + Alembic)        │
│                │                                    │
│  SkillAgent    │         PostgreSQL                  │
│  MatchAgent    │    candidates · positions ·        │
│  GapAgent      │    skills · extractions ·          │
│                │    recommendations                  │
└────────────────┴────────────────────────────────────┘
                        │
              ┌─────────▼──────────┐
              │   Anthropic API    │
              │ claude-sonnet-4-6  │
              └────────────────────┘
```

---

## 3. Technology Stack

| Layer | Technology | Reason |
|-------|-----------|--------|
| Runtime | Python 3.11+ | Standard for AI/agentic work |
| API Framework | FastAPI | Auto OpenAPI docs, async support, Pydantic v2 |
| AI Orchestration | LangGraph 0.2+ | Multi-node graphs, stateful agents, conditional edges |
| LLM | Claude claude-sonnet-4-6 via Anthropic SDK | Framework requirement; best reasoning at cost |
| Database | PostgreSQL 15 | Matches Perficient platform architecture |
| ORM | SQLAlchemy 2.0 (async) | Type-safe, async-native |
| Migrations | Alembic | Reproducible schema changes |
| Frontend | React 18 + TypeScript + Vite | Modern, type-safe UI |
| UI Components | shadcn/ui + TailwindCSS | Fast, accessible, professional |
| Containerization | Docker + Docker Compose | Reproducible local dev |
| Testing | pytest + pytest-asyncio | API + agent integration tests |

---

## 4. Data Models

### 4.1 Candidate

```python
class Candidate:
    id: UUID (PK)
    full_name: str
    email: str (unique)
    years_of_experience: int
    current_role_title: str
    summary: str | None
    created_at: datetime
    updated_at: datetime
    skills: List[CandidateSkill]  # one-to-many
```

### 4.2 CandidateSkill

```python
class CandidateSkill:
    id: UUID (PK)
    candidate_id: UUID (FK → Candidate)
    skill_name: str          # e.g. "Angular", "React", ".NET"
    category: SkillCategory  # enum
    proficiency: Proficiency # enum
    years_used: int | None
```

### 4.3 SkillCategory (enum)

```
frontend | backend | cloud | devops | database | 
mobile | testing | architecture | soft_skill | other
```

### 4.4 Proficiency (enum, ordered)

```
beginner < intermediate < advanced < expert
```

### 4.5 Position

```python
class Position:
    id: UUID (PK)
    title: str
    department: str
    seniority: Seniority     # enum: junior | mid | senior | lead | principal
    status: PositionStatus   # enum: open | on_hold | filled | closed
    description_raw: str     # raw JD text
    ai_summary: str | None   # AI-generated role summary
    ai_seniority_suggestion: str | None
    created_at: datetime
    updated_at: datetime
    required_skills: List[PositionSkill]  # one-to-many
```

### 4.6 PositionSkill

```python
class PositionSkill:
    id: UUID (PK)
    position_id: UUID (FK → Position)
    skill_name: str
    category: SkillCategory
    is_required: bool        # True = required, False = preferred
    min_proficiency: Proficiency
    confidence: Confidence   # enum: high | medium | low (AI confidence)
    source: str              # "manual" | "ai_extracted"
```

### 4.7 ExtractionHistory

```python
class ExtractionHistory:
    id: UUID (PK)
    position_id: UUID (FK → Position)
    extracted_at: datetime
    skills_snapshot: JSON    # snapshot of extracted skills before replacement
    agent_trace: JSON | None # LangGraph node execution log
```

### 4.8 RecommendationResult

```python
class RecommendationResult:
    id: UUID (PK)
    position_id: UUID (FK)
    candidate_id: UUID (FK)
    generated_at: datetime
    match_score: float       # 0.0 – 100.0
    matched_skills: JSON
    missing_skills: JSON
    partial_skills: JSON
    rationale: str           # AI-generated text
    suitability_verdict: str # Strong | Moderate | Weak | Not Suitable
```

---

## 5. API Endpoints

### Candidates

| Method | Path | Description | Story |
|--------|------|-------------|-------|
| POST | `/api/v1/candidates` | Create candidate profile | US-101 |
| GET | `/api/v1/candidates/{id}` | Get candidate profile | US-104 |
| PATCH | `/api/v1/candidates/{id}` | Update candidate profile | US-102 |
| GET | `/api/v1/candidates` | Search talent bank | US-103 |
| DELETE | `/api/v1/candidates/{id}` | Remove candidate | — |

### Positions

| Method | Path | Description | Story |
|--------|------|-------------|-------|
| POST | `/api/v1/positions` | Create position | US-201 |
| GET | `/api/v1/positions/{id}` | Get position detail | — |
| PATCH | `/api/v1/positions/{id}` | Update position | US-202 |
| GET | `/api/v1/positions` | List positions | US-203 |

### AI — Skill Extraction

| Method | Path | Description | Story |
|--------|------|-------------|-------|
| POST | `/api/v1/extract-skills` | Extract skills from raw JD text | US-301 |
| POST | `/api/v1/positions/{id}/extract-skills` | Extract + apply to position | US-301/302 |

### AI — Recommendations

| Method | Path | Description | Story |
|--------|------|-------------|-------|
| POST | `/api/v1/positions/{id}/recommend-candidates` | Rank candidates for position | US-401 |
| POST | `/api/v1/candidates/{id}/recommend-positions` | Rank positions for candidate | US-402 |

### AI — Gap Analysis

| Method | Path | Description | Story |
|--------|------|-------------|-------|
| POST | `/api/v1/gap-analysis` | Analyze gap: candidate vs position | US-501 |
| POST | `/api/v1/positions/{id}/batch-gap-analysis` | Gap analysis for top N candidates | US-502 |

---

## 6. LangGraph Agent Graphs

### 6.1 SkillExtractionGraph

**Input state:** `{ jd_text: str, position_id: UUID | None }`  
**Output state:** `{ skills: List[ExtractedSkill], summary: str, suggested_seniority: str, trace: List[NodeLog] }`

```
START
  │
  ▼
parse_jd          — chunk text, detect language, remove boilerplate
  │
  ▼
extract_skills    — Claude call: extract skill list as structured JSON
  │
  ▼
validate_schema   — check output against Pydantic model; retry if invalid (max 2)
  │
  ▼
classify_skills   — assign category and confidence based on skill names
  │
  ▼
generate_summary  — Claude call: produce role summary + seniority suggestion
  │
  ▼
END
```

**Retry logic:** `validate_schema` node uses a conditional edge — if schema invalid, loops back to `extract_skills` with a correction prompt, up to 2 retries before returning a partial result.

---

### 6.2 MatchRecommendationGraph

**Input state:** `{ position_id: UUID, candidates: List[CandidateProfile], top_n: int }`  
**Output state:** `{ ranked_recommendations: List[RecommendationResult], trace: List[NodeLog] }`

```
START
  │
  ▼
load_position_skills    — fetch required skills + seniority from DB
  │
  ▼
score_all_candidates    — for each candidate: compute match score (deterministic)
  │
  ▼
apply_seniority_filter  — down-weight candidates whose experience doesn't fit level
  │
  ▼
rank_candidates         — sort descending by score, take top N
  │
  ▼
generate_rationales     — Claude batch call: write rationale for each top candidate
  │
  ▼
compile_report          — assemble final ranked list with all metadata
  │
  ▼
END
```

**Scoring algorithm (deterministic, no LLM):**

```
base_score = (matched_required_skills / total_required_skills) * 70
proficiency_bonus = sum(proficiency_score_delta) / max_possible * 20
preferred_bonus = (matched_preferred_skills / total_preferred_skills) * 10
final_score = base_score + proficiency_bonus + preferred_bonus

proficiency_score: beginner=1, intermediate=2, advanced=3, expert=4
proficiency_score_delta = candidate_level - required_level (clamped to 0 if negative)
```

---

### 6.3 GapAnalysisGraph

**Input state:** `{ candidate_id: UUID, position_id: UUID }`  
**Output state:** `{ fully_matched: List, partial: List, missing: List, verdict: str, recommendations: List[str], trace: List[NodeLog] }`

```
START
  │
  ▼
load_pair             — fetch candidate skills + position requirements
  │
  ▼
diff_skills           — deterministic: produce matched / partial / missing buckets
  │
  ▼
assess_seniority_fit  — compare years_of_experience vs seniority expectations
  │
  ▼
generate_gap_report   — Claude call: generate learning recommendations per gap
  │
  ▼
produce_verdict       — rule-based: Strong / Moderate / Weak / Not Suitable
  │
  ▼
END
```

**Verdict rules:**
- Strong Match: score ≥ 85 and seniority fits
- Moderate Match: score 60–84 OR seniority adjacent
- Weak Match: score 40–59
- Not Suitable: score < 40

---

## 7. Claude Prompt Strategy

All Claude calls use **prompt caching** on the system prompt (static instruction block), with the dynamic content (JD text, candidate data) passed in the human turn.

### 7.1 Skill Extraction Prompt (System — Cached)

```
You are a technical recruiter assistant specializing in software engineering roles.
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
```

### 7.2 Match Rationale Prompt (System — Cached)

```
You are a technical recruiter AI. You will receive a candidate's skill profile 
and a position's requirements. Your job is to write a concise, honest rationale 
(3-4 sentences) explaining why this candidate is or is not a strong match.

Be specific about which skills match, which are missing, and what the main 
strengths and concerns are. Do not speculate about skills not in the profile.
```

### 7.3 Gap Analysis Prompt (System — Cached)

```
You are a technical career advisor. You will receive a structured skill gap analysis 
between a candidate and a position. For each missing or partial skill, provide a 
specific, actionable development recommendation.

Format each recommendation as:
- Skill: [skill name]
  Gap: [what's missing]
  Recommendation: [specific action, estimated timeframe]

Keep recommendations realistic and focused on software engineering growth paths.
```

---

## 8. Project Structure

```
capstone/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── candidates.py
│   │   │   │   ├── positions.py
│   │   │   │   ├── extraction.py
│   │   │   │   ├── recommendations.py
│   │   │   │   └── gap_analysis.py
│   │   ├── agents/
│   │   │   ├── skill_extraction_graph.py
│   │   │   ├── match_recommendation_graph.py
│   │   │   └── gap_analysis_graph.py
│   │   ├── models/
│   │   │   └── db.py               # SQLAlchemy models
│   │   ├── schemas/
│   │   │   └── api.py              # Pydantic request/response schemas
│   │   ├── services/
│   │   │   ├── candidate_service.py
│   │   │   ├── position_service.py
│   │   │   └── agent_service.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── database.py
│   │   └── main.py
│   ├── alembic/
│   │   └── versions/
│   ├── tests/
│   │   ├── test_candidates_api.py
│   │   ├── test_positions_api.py
│   │   ├── test_skill_extraction_agent.py
│   │   ├── test_match_agent.py
│   │   └── test_gap_analysis_agent.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Candidates.tsx
│   │   │   ├── Positions.tsx
│   │   │   ├── ExtractSkills.tsx
│   │   │   └── GapAnalysis.tsx
│   │   ├── components/
│   │   ├── api/
│   │   │   └── client.ts
│   │   └── App.tsx
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── specs/
│   ├── user-stories.md          ← this file's sibling
│   ├── technical-spec.md        ← this file
│   └── development-plan.md
└── README.md
```

---

## 9. Environment Variables

```env
# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Database
DATABASE_URL=postgresql+asyncpg://talentmatch:password@localhost:5432/talentmatch

# App
APP_ENV=development
SECRET_KEY=...
LOG_LEVEL=INFO

# LangGraph
LANGGRAPH_TRACING=true
```

---

## 10. Capstone Alignment

| Capstone Criterion | How This Project Addresses It |
|--------------------|-------------------------------|
| Applied AI capability | Three distinct LangGraph agentic graphs with multi-node reasoning |
| Real-world business contribution | Solves actual talent matching pain for consulting firms like Perficient |
| Claude usage | claude-sonnet-4-6 with prompt caching, structured JSON outputs, multi-turn reasoning |
| Platform tech alignment | LangGraph + Claude + PostgreSQL = exact stack shown in AI DLC and AI TLC platforms |
| Measurable outcomes | Match scores, extraction confidence, gap counts — all quantifiable |
| Evidence for submission | API, working demo, agent trace logs, test results |
