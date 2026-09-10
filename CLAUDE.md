# TalentMatch AI — Claude Code Guide

AI-powered talent intelligence platform for software engineering roles.
Capstone project for Perficient Global AI First Academy (Option 04 — Case Study AI Challenge).

## Project Purpose

Helps companies manage a talent bank of software engineers and open engineering positions.
Uses LangGraph + Claude to extract skills from job descriptions, recommend candidates for positions, and perform skill gap analysis.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API | Python 3.11 · FastAPI · Uvicorn |
| AI Orchestration | LangGraph 0.2+ · Anthropic SDK |
| LLM | Claude claude-sonnet-4-6 (with prompt caching) |
| Database | PostgreSQL 15 · SQLAlchemy 2.0 (async) · Alembic |
| Frontend | React 18 · TypeScript · Vite · TailwindCSS · shadcn/ui |
| Dev Infra | Docker · Docker Compose |
| Testing | pytest · pytest-asyncio · httpx |

## Project Structure

```
capstone/
├── CLAUDE.md                  ← you are here
├── docker-compose.yml
├── specs/
│   ├── user-stories.md        ← 18 user stories across 6 epics
│   ├── technical-spec.md      ← data models, API endpoints, agent graph designs
│   └── development-plan.md    ← 4 phases with tasks and definitions of done
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/v1/            ← FastAPI routers
│   │   ├── agents/            ← LangGraph graphs
│   │   │   ├── base.py
│   │   │   ├── skill_extraction_graph.py
│   │   │   ├── match_recommendation_graph.py
│   │   │   └── gap_analysis_graph.py
│   │   ├── models/db.py       ← SQLAlchemy ORM models
│   │   ├── schemas/api.py     ← Pydantic request/response schemas
│   │   ├── services/          ← business logic layer
│   │   └── core/              ← config, DB session, LLM client
│   ├── alembic/versions/
│   ├── tests/
│   ├── seed.py
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── pages/
    │   ├── components/
    │   └── api/client.ts
    └── package.json
```

## Key Commands

```bash
# Start full stack
docker compose up

# Backend only (dev, with hot reload)
cd backend && uvicorn app.main:app --reload --port 8000

# Run migrations
cd backend && alembic upgrade head

# Create a new migration
cd backend && alembic revision --autogenerate -m "description"

# Run tests
cd backend && pytest

# Run tests with output
cd backend && pytest -v -s

# Seed the database
cd backend && python seed.py

# Frontend dev server
cd frontend && npm run dev
```

## API Documentation

Once the backend is running: http://localhost:8000/docs (Swagger UI)

## Environment Variables

Required in `backend/.env`:
```
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=postgresql+asyncpg://talentmatch:password@localhost:5432/talentmatch
APP_ENV=development
LOG_LEVEL=INFO
```

## Working Method

**Always plan before coding.** Before writing or editing any code, state:
1. Which user story or task this addresses (reference the US-xxx or P#-T# ID)
2. Which files will be created or modified
3. What the approach is and why

Only proceed with implementation after the plan is stated. If the scope is unclear, ask before planning. This keeps changes traceable back to specs and prevents drifting outside the intended scope.

## Development Conventions

- **Spec-driven:** Check `specs/user-stories.md` for acceptance criteria before implementing any feature. Every API endpoint maps to a US-xxx story.
- **Async throughout:** All DB calls use `async with session` via SQLAlchemy async engine. No sync DB calls.
- **Enums are ordered:** `Proficiency` enum has a defined order (beginner < intermediate < advanced < expert). Comparisons must respect this.
- **No LLM for scoring:** The candidate scoring algorithm in `services/scoring.py` is fully deterministic. Claude is only called for: skill extraction, rationale generation, gap recommendations.
- **Prompt caching:** Every Claude call uses `cache_control: {"type": "ephemeral"}` on the system prompt block. Never skip this.
- **Agent traces:** Every LangGraph node must log: node name, input summary, output summary, and duration. Use the `NodeLogger` utility from `agents/base.py`.
- **Error shapes:** All API errors must follow `{"detail": "...", "code": "..."}` — use the shared error handler in `core/errors.py`.
- **Migrations:** Never edit DB models without creating an Alembic migration. Run `alembic check` before committing.

## LangGraph Agent Graphs

Three graphs, each in its own file under `app/agents/`:

| Graph | File | Triggered by |
|-------|------|-------------|
| SkillExtractionGraph | `skill_extraction_graph.py` | `POST /extract-skills` |
| MatchRecommendationGraph | `match_recommendation_graph.py` | `POST /positions/{id}/recommend-candidates` |
| GapAnalysisGraph | `gap_analysis_graph.py` | `POST /gap-analysis` |

See `specs/technical-spec.md` §6 for the full node-by-node design of each graph.

## Specs Reference

- User stories with acceptance criteria: `specs/user-stories.md`
- Data models, API table, agent graph designs, Claude prompts: `specs/technical-spec.md`
- Phase-by-phase task list: `specs/development-plan.md`

## Custom Commands

Use these slash commands for context-aware help in this project:

| Command | Purpose |
|---------|---------|
| `/backend` | FastAPI routes, services, Pydantic schemas |
| `/agent` | LangGraph graph implementation, Claude calls |
| `/database` | SQLAlchemy models, Alembic migrations, queries |
| `/frontend` | React pages, components, API client |
| `/testing` | pytest, test structure, integration test patterns |
| `/seed` | Seed data generation for candidates and positions |
