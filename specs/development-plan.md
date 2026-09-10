# TalentMatch AI — Development Plan

**Project:** AI-Powered Talent Intelligence Platform  
**Methodology:** Spec-Driven Development · Phased Delivery  

---

## Phases Overview

| Phase | Focus | Deliverable |
|-------|-------|-------------|
| Phase 1 | Foundation & Data Layer | Repo, DB schema, CRUD APIs, Docker setup |
| Phase 2 | AI Skill Extraction Agent | LangGraph SkillExtractionGraph + extraction API |
| Phase 3 | AI Matching & Gap Analysis Agents | MatchRecommendationGraph + GapAnalysisGraph |
| Phase 4 | Frontend Dashboard & Capstone Packaging | React UI, integration, demo data, submission prep |

---

## Phase 1 — Foundation & Data Layer

**Goal:** A fully working CRUD backend. No AI yet. Everything testable via Swagger.

### Tasks

#### P1-T1 · Project Scaffold
- [x] Initialize Git repository with `.gitignore` (Python, Node)
- [x] Create `docker-compose.yml` with services: `api`, `db` (PostgreSQL 15), `frontend`
- [x] Create `backend/` with FastAPI app skeleton (`main.py`, `core/config.py`, `core/database.py`)
- [x] Configure Pydantic settings from environment variables
- [x] Verify `docker compose up` starts successfully with a `/health` endpoint

#### P1-T2 · Database Schema
- [x] Define SQLAlchemy 2.0 async models: `Candidate`, `CandidateSkill`, `Position`, `PositionSkill`, `ExtractionHistory`, `RecommendationResult`
- [x] Initialize Alembic; create first migration
- [x] Verify migration applies cleanly: `alembic upgrade head`

#### P1-T3 · Pydantic Schemas
- [x] Define request/response schemas for all entities (create, update, read)
- [x] Define enums: `SkillCategory`, `Proficiency`, `Seniority`, `PositionStatus`, `Confidence`
- [x] Ensure all schemas have proper validation rules matching acceptance criteria

#### P1-T4 · Candidate CRUD API
- [x] `POST /api/v1/candidates` — create with skills list (US-101)
- [x] `GET /api/v1/candidates/{id}` — fetch profile (US-104)
- [x] `PATCH /api/v1/candidates/{id}` — update profile + skills (US-102)
- [x] `GET /api/v1/candidates` — search with filters: skill_name, category, min_proficiency (US-103)
- [x] `DELETE /api/v1/candidates/{id}`
- [x] Unit tests: `tests/test_candidates_api.py` (happy path + error cases)

#### P1-T5 · Position CRUD API
- [x] `POST /api/v1/positions` — create (US-201)
- [x] `GET /api/v1/positions/{id}` — fetch
- [x] `PATCH /api/v1/positions/{id}` — update (US-202)
- [x] `GET /api/v1/positions` — list with filters: status, seniority (US-203)
- [x] Unit tests: `tests/test_positions_api.py`

#### P1-T6 · Seed Data
- [x] Create a `seed.py` script that populates:
  - 10 candidate profiles (realistic, covering Angular+.NET, React, Node.js, Java, DevOps profiles)
  - 5 open positions (matching the skill areas above)
- [x] Include a mix of seniority levels and proficiency gaps

**Phase 1 Definition of Done:**
- All CRUD endpoints return correct responses verified via Swagger UI
- All migrations run cleanly from scratch
- Test suite passes with no failures
- `docker compose up` boots the full stack

---

## Phase 2 — AI Skill Extraction Agent

**Goal:** A working LangGraph agent that takes raw JD text and returns structured skills.

### Tasks

#### P2-T1 · Anthropic SDK Setup
- [x] Add `anthropic` to `requirements.txt`
- [x] Create `app/core/llm.py` with a configured Anthropic client (with prompt caching)
- [x] Verify API key works with a simple test call

#### P2-T2 · LangGraph Setup
- [x] Add `langgraph`, `langchain-anthropic` to `requirements.txt`
- [x] Create `app/agents/` package
- [x] Create `app/agents/base.py` with shared state types and node logging utilities
- [ ] Verify LangGraph imports work correctly

#### P2-T3 · SkillExtractionGraph Implementation
- [x] Define `ExtractionState` TypedDict with all input/output fields
- [x] Implement node `parse_jd`: clean text, detect encoding issues, basic chunking
- [x] Implement node `extract_skills`: Claude call with cached system prompt; parse JSON response
- [x] Implement node `validate_schema`: Pydantic validation of Claude output; set retry flag if invalid
- [x] Implement conditional edge: if invalid and retries < 2, loop back to `extract_skills` with correction context
- [x] Implement node `classify_skills`: map raw skill names to `SkillCategory` enum (rule-based lookup table)
- [x] Implement node `generate_summary`: Claude call for role summary and seniority suggestion
- [x] Compile the graph and verify it runs end-to-end with a sample JD

#### P2-T4 · Skill Extraction API Endpoints
- [x] `POST /api/v1/extract-skills` — standalone extraction, returns structured result (US-301)
- [x] `POST /api/v1/positions/{id}/extract-skills` — extract and apply to position (US-302)
  - Stores previous skills in `ExtractionHistory` before overwriting
  - Updates `position.required_skills` and `position.ai_summary`
- [x] Integration tests: `tests/test_skill_extraction_agent.py`
  - Test with a well-formed JD (Angular + .NET fullstack)
  - Test with a vague/short JD (retry path)
  - Test with a React frontend JD

#### P2-T5 · Prompt Caching Verification
- [x] Add logging to confirm cache hit vs. miss on repeated calls
- [x] Document cache hit rate in test output

**Phase 2 Definition of Done:**
- SkillExtractionGraph runs successfully for 3+ different JD samples
- Extraction API endpoints tested via Swagger
- Retry logic verified with a deliberately malformed prompt output
- Prompt cache confirmed working (second call for same system prompt shows cache hit)

---

## Phase 3 — Matching & Gap Analysis Agents

**Goal:** The two core AI recommendation flows working end-to-end.

### Tasks

#### P3-T1 · Match Scoring Engine (Deterministic)
- [x] Create `app/services/scoring.py`
- [x] Implement `score_candidate(candidate, position) -> ScoringResult`
  - base_score: required skills match percentage × 70
  - proficiency_bonus: proficiency delta sum × 20
  - preferred_bonus: preferred skills match × 10
- [x] Unit test scoring edge cases: exact match, zero match, partial proficiency

#### P3-T2 · MatchRecommendationGraph Implementation
- [x] Define `MatchState` TypedDict
- [x] Implement node `load_position_skills`: fetch from DB via service
- [x] Implement node `score_all_candidates`: call `scoring.py` for each candidate
- [x] Implement node `apply_seniority_filter`: apply experience-based weight adjustment
- [x] Implement node `rank_candidates`: sort, take top N, produce matched/missing/partial lists
- [x] Implement node `generate_rationales`: batched Claude call for top N rationales (1 API call with multiple candidates in context, not N separate calls)
- [x] Implement node `compile_report`: assemble `RecommendationResult` objects and persist to DB
- [ ] Compile and test graph

#### P3-T3 · Recommendation API Endpoints
- [x] `POST /api/v1/positions/{id}/recommend-candidates` (US-401)
  - Query param: `top_n` (default 5)
  - Returns ranked list with scores, matched/missing skills, rationale
- [x] `POST /api/v1/candidates/{id}/recommend-positions` (US-402)
  - Reuses scoring engine, inverted: score position fit for candidate
- [x] Integration tests: `tests/test_match_agent.py`
  - Test with seed data, verify top candidate is the correct best match
  - Test with no matching candidates, verify graceful empty result

#### P3-T4 · GapAnalysisGraph Implementation
- [x] Define `GapState` TypedDict
- [x] Implement node `load_pair`: fetch candidate + position from DB
- [x] Implement node `diff_skills`: produce `fully_matched`, `partial`, `missing` lists (deterministic)
- [x] Implement node `assess_seniority_fit`: check years_of_experience against seniority norms
- [x] Implement node `generate_gap_report`: Claude call with cached system prompt; one recommendation per gap
- [x] Implement node `produce_verdict`: rule-based verdict from score thresholds
- [ ] Compile and test graph

#### P3-T5 · Gap Analysis API Endpoints
- [x] `POST /api/v1/gap-analysis` — body: `{ candidate_id, position_id }` (US-501)
- [x] `POST /api/v1/positions/{id}/batch-gap-analysis` — query param: `top_n` (US-502)
- [x] Integration tests: `tests/test_gap_analysis_agent.py`
  - Test strong match: candidate with all skills
  - Test weak match: candidate with no matching skills
  - Test partial: candidate with skills at wrong proficiency level

**Phase 3 Definition of Done:**
- Both recommendation endpoints return sensible, ranked results with seed data
- Gap analysis returns correct bucket splits (verified against known test cases)
- All verdicts consistent with scoring thresholds
- Agent trace logs visible in server output for each graph run

---

## Phase 4 — Frontend Dashboard & Capstone Packaging

**Goal:** Working React dashboard, polished demo, and submission-ready artifacts.

### Tasks

#### P4-T1 · Frontend Scaffold
- [ ] Initialize React 18 + TypeScript + Vite project in `frontend/`
- [ ] Add TailwindCSS + shadcn/ui
- [ ] Configure API client (`src/api/client.ts`) pointing to FastAPI backend
- [ ] Add React Router for page navigation
- [ ] Verify frontend boots and can call `/health`

#### P4-T2 · Talent Bank Pages
- [ ] Candidate list page with search/filter controls (US-103)
- [ ] Candidate profile view with full skill list (US-104)
- [ ] Add/Edit candidate form with dynamic skill rows (US-101, US-102)

#### P4-T3 · Position Pages
- [ ] Position list grouped by status (US-203, US-602)
- [ ] Position detail page showing required skills
- [ ] Add position form with JD text area (US-201)

#### P4-T4 · AI Extraction Interface
- [ ] Standalone "Extract Skills from JD" page (US-603)
  - Large textarea for JD input
  - Submit triggers `POST /api/v1/extract-skills`
  - Results displayed as editable skill table
  - "Apply to Position" button available
- [ ] Position detail: "Re-extract Skills" button (US-302)

#### P4-T5 · Recommendation Interface
- [ ] "Find Candidates" button on position detail → calls recommend-candidates (US-401)
- [ ] Results shown as ranked cards with: match score bar, matched skills chips, rationale (collapsed/expanded) (US-604)
- [ ] "Find Positions" on candidate profile → calls recommend-positions (US-402)

#### P4-T6 · Gap Analysis Interface
- [ ] Gap analysis view: select candidate + position → show buckets side by side
- [ ] Verdict badge (Strong / Moderate / Weak / Not Suitable) prominently displayed
- [ ] Recommendations listed per missing skill

#### P4-T7 · Dashboard Summary (US-601)
- [ ] Stat cards: total candidates, total open positions, top skills in bank
- [ ] Recent candidates list

#### P4-T8 · Capstone Submission Prep
- [ ] Write `README.md` with: project overview, architecture diagram, setup instructions, demo walkthrough
- [ ] Record a short demo video script (key flows to show)
- [ ] Populate seed data with 15+ realistic engineering candidates and 6+ positions
- [ ] Verify all acceptance criteria from user-stories.md are met
- [ ] Ensure OpenAPI docs at `/docs` are complete and accurate
- [ ] Final pass on NFRs (response times, caching, logging)

**Phase 4 Definition of Done:**
- Full demo flow works: create position → paste JD → extract skills → get recommendations → view gap analysis
- All six dashboard pages render correctly
- Seed data produces meaningful, realistic recommendation results
- README is clear enough for an evaluator to run the project in under 10 minutes

---

## Capstone Submission Checklist

| Item | Description |
|------|-------------|
| Working application | Docker Compose boots full stack cleanly |
| AI capability evidence | Three LangGraph agent graphs with observable traces |
| Claude usage | Skill extraction, rationale generation, gap recommendations |
| Prompt caching | Documented cache hit rate in test output |
| Business impact | Demonstrates measurable: match scores, gap counts, time-to-shortlist |
| Code quality | Alembic migrations, type-safe schemas, integration tests |
| Documentation | README + OpenAPI Swagger |
| Submission format | GitHub repo link + evidence write-up |

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Claude API rate limits during batch rationale generation | Medium | Batch candidates in a single call; add exponential backoff |
| LangGraph schema changes between versions | Low | Pin exact version in requirements.txt |
| Complex SQL for skill-based search | Low | Use SQLAlchemy ORM with array unnesting; test early |
| JD text causing Claude to hallucinate skills | Medium | Prompt explicitly forbids inventing skills; validate_schema node catches malformed output |
| Frontend complexity running over time | Medium | Start with API-only demo; frontend is additive |
