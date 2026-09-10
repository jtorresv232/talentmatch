# TalentMatch AI

AI-powered talent intelligence platform for software engineering roles.  
Capstone project — **Perficient Global AI First Academy · Option 04 Case Study AI Challenge**

---

## Overview

TalentMatch AI helps recruiting teams manage a talent bank of software engineers and open engineering positions. It uses **LangGraph + Claude** to:

- Extract structured skills from job descriptions with AI
- Score and rank candidates against open positions deterministically
- Generate natural-language rationale and gap analysis with Claude
- Surface skill gaps and learning recommendations per candidate–position pair

---

## Setup

### Prerequisites

- Docker Desktop
- An Anthropic API key (`sk-ant-…`)

### 1. Clone and configure

```bash
git clone https://github.com/jtorresv232/talentmatch.git
cd talentmatch
```

Create `backend/.env`:

```env
ANTHROPIC_API_KEY=sk-ant-YOUR_KEY_HERE
DATABASE_URL=postgresql+asyncpg://talentmatch:password@db:5432/talentmatch
APP_ENV=development
LOG_LEVEL=INFO
```

### 2. Start the stack

```bash
docker compose up --build
```

Services:
- Frontend → http://localhost:5173
- API → http://localhost:8000
- API docs → http://localhost:8000/docs

### 3. Run database migrations

```bash
docker compose exec api alembic upgrade head
```

### 4. Seed sample data (16 candidates · 8 positions)

```bash
docker compose exec api python seed.py
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Browser (React 18 + TypeScript + Vite + TailwindCSS)   │
└───────────────────┬─────────────────────────────────────┘
                    │ HTTP /api/v1/*  (proxied by Vite dev server)
┌───────────────────▼─────────────────────────────────────┐
│          FastAPI  (Python 3.11 · Uvicorn · async)        │
│                                                          │
│  Routers → Services → LangGraph Agents                   │
│                          │                               │
│           ┌──────────────▼──────────────┐               │
│           │   Anthropic API (Claude     │               │
│           │   claude-sonnet-4-6 with    │               │
│           │   prompt caching)           │               │
│           └─────────────────────────────┘               │
│                                                          │
│  SQLAlchemy 2.0 (async) · Alembic migrations             │
└───────────────────┬─────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────┐
│             PostgreSQL 15                                │
└─────────────────────────────────────────────────────────┘
```

### LangGraph Agent Graphs

| Graph | Trigger | Purpose |
|-------|---------|---------|
| `SkillExtractionGraph` | `POST /extract-skills` | Parses JD → validates → classifies → summarises |
| `MatchRecommendationGraph` | `POST /positions/{id}/recommend-candidates` | Scores all candidates → filters → ranks → generates rationale |
| `GapAnalysisGraph` | `POST /gap-analysis` | Diffs skills → assesses seniority → generates recommendations |

Scoring is **fully deterministic** (no LLM). Claude is called only for: skill extraction, rationale text, and gap recommendations.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API | Python 3.11 · FastAPI · Uvicorn |
| AI Orchestration | LangGraph 0.2+ · Anthropic SDK |
| LLM | Claude claude-sonnet-4-6 (prompt caching on every system prompt) |
| Database | PostgreSQL 15 · SQLAlchemy 2.0 (async) · Alembic |
| Frontend | React 18 · TypeScript · Vite · TailwindCSS · shadcn/ui |
| Dev Infra | Docker · Docker Compose |
| Testing | pytest · pytest-asyncio · Vitest · Testing Library |

---

## Demo Walkthrough

### Flow 1 — Add a candidate manually

1. Open **Talent Bank** → **Add Candidate**
2. Fill in name, email, role, years of experience
3. Add skill rows (name, category, proficiency, years used)
4. Save → lands on the candidate profile page

### Flow 2 — Create a position and extract skills with AI

1. Open **Positions** → **Add Position**
2. Fill in title, department, seniority; paste the full job description
3. Save → lands on the position detail page
4. Click **Re-extract Skills** → AI extracts structured skills from the JD
5. Skills table populates automatically

### Flow 3 — Find matching candidates for a position

1. On any position detail page, click **Find Candidates**
2. The system scores every candidate deterministically against the position's required skills
3. Claude generates a natural-language rationale for each top result
4. Results appear ranked by match score (0–100) with verdict badges, matched/missing skill chips, and collapsible rationale

### Flow 4 — Gap analysis

1. Open **Gap Analysis** from the nav
2. Select any candidate and any position from the dropdowns
3. Click **Run Gap Analysis**
4. The LangGraph graph diffs skills, checks seniority, and calls Claude for recommendations
5. Results show: verdict badge, score bar, Matched / Partial / Missing skill buckets, numbered recommendations

### Flow 5 — Standalone skill extraction

1. Open **Extract Skills** from the nav
2. Paste any job description
3. Click **Extract Skills**
4. Review the extracted skill table (category, proficiency, required/preferred, confidence)
5. Optionally apply the extracted skills to an open position via the dropdown

---

## Project Structure

```
talentmatch/
├── backend/
│   ├── app/
│   │   ├── agents/          # LangGraph graphs
│   │   ├── api/v1/          # FastAPI routers
│   │   ├── core/            # Config, DB, LLM client, errors
│   │   ├── models/db.py     # SQLAlchemy ORM models
│   │   ├── schemas/api.py   # Pydantic request/response schemas
│   │   └── services/        # Business logic (scoring, recommendations, gap analysis)
│   ├── tests/               # pytest integration tests
│   ├── alembic/             # DB migrations
│   └── seed.py              # Sample data (16 candidates, 8 positions)
├── frontend/
│   └── src/
│       ├── pages/           # Dashboard, Candidates, Positions, ExtractSkills, GapAnalysis
│       ├── components/ui/   # shadcn/ui primitives
│       └── api/client.ts    # Typed Axios API client
└── specs/
    ├── user-stories.md      # 18 user stories across 6 epics
    ├── technical-spec.md    # Data models, API table, agent graph designs
    └── development-plan.md  # Phase-by-phase task list (all phases complete)
```

---

## Key Design Decisions

- **Deterministic scoring, LLM for language** — The match score is computed with a fixed formula (skill coverage 70%, proficiency delta 20%, preferred skills 10%). Claude is only invoked for natural-language outputs. This makes scores reproducible and auditable.
- **Prompt caching** — Every Claude call attaches `cache_control: ephemeral` to the system prompt block, reducing latency and cost on repeated calls.
- **Async throughout** — All database access uses SQLAlchemy's async engine with `async with session`. No sync DB calls anywhere.
- **Bulk skill replacement** — Updating a candidate's or position's skills uses a single `DELETE` statement rather than individual ORM deletions, avoiding SQLAlchemy identity-map stale-data issues.
- **Agent tracing** — Every LangGraph node logs its name, input summary, output summary, and duration via `NodeLogger`. Trace data is returned in API responses for observability.
