# TalentMatch AI — User Stories

**Project:** AI-Powered Talent Intelligence Platform for Software Engineering Roles  
**Capstone Track:** Perficient Global AI First Academy — Option 04 Case Study AI Challenge  
**Tech Stack:** Python · FastAPI · Claude (claude-sonnet-4-6) · LangGraph · PostgreSQL · React

---

## Epics Overview

| # | Epic | Description |
|---|------|-------------|
| E1 | Talent Profile Management | Register and maintain people with their skills |
| E2 | Position Management | Register and maintain open engineering positions |
| E3 | AI Skill Extraction | Parse job descriptions and extract structured skills using AI |
| E4 | Profile Recommendation | AI-driven matching of candidates to open positions |
| E5 | Skill Gap Analysis | Identify what a candidate is missing for a given position |
| E6 | Recruiter Dashboard | Unified view for recruiters to work with the system |

---

## E1 — Talent Profile Management

### US-101 · Register a Candidate Profile

**As a** recruiter or HR operator,  
**I want to** register a person's profile with their skills and experience,  
**so that** they are discoverable for open positions.

**Acceptance Criteria:**
- AC1: I can submit a profile with: full name, email, years of experience, current role title, and a list of skills (each with proficiency level: beginner / intermediate / advanced / expert).
- AC2: Each skill entry captures: skill name, category (frontend / backend / cloud / devops / database / soft-skill / other), and proficiency level.
- AC3: The system returns a unique candidate ID upon successful creation.
- AC4: Email must be unique — duplicate registration is rejected with a clear error.
- AC5: Profile creation succeeds without requiring AI processing (pure CRUD).

**Example skills for a fullstack engineer:**
- Angular — frontend — advanced
- .NET / C# — backend — expert
- SQL Server — database — intermediate
- Azure — cloud — beginner

---

### US-102 · Update a Candidate Profile

**As a** recruiter,  
**I want to** update an existing candidate's skills or information,  
**so that** the profile reflects their current capabilities.

**Acceptance Criteria:**
- AC1: I can update any field including adding, removing, or changing proficiency of skills.
- AC2: A timestamp is recorded on every update.
- AC3: The system returns the updated profile in the response.

---

### US-103 · Search the Talent Bank

**As a** recruiter,  
**I want to** search the talent bank by skill name, category, or proficiency level,  
**so that** I can find candidates with specific capabilities.

**Acceptance Criteria:**
- AC1: I can filter by one or more skill names (e.g., "React", "Angular").
- AC2: I can filter by skill category (e.g., "frontend").
- AC3: I can filter by minimum proficiency level (e.g., "at least intermediate").
- AC4: Results include candidate name, current role, years of experience, and matching skills.
- AC5: Results are paginated (default 20 per page).

---

### US-104 · View a Candidate Profile

**As a** recruiter,  
**I want to** view the full profile of a candidate,  
**so that** I can evaluate them in detail.

**Acceptance Criteria:**
- AC1: The profile view shows all personal info, complete skill list with proficiencies, and profile creation/update timestamps.
- AC2: If no candidate is found for the given ID, a 404 response is returned.

---

## E2 — Position Management

### US-201 · Register an Open Position

**As a** recruiter or hiring manager,  
**I want to** register an open engineering position,  
**so that** the system can help find matching candidates.

**Acceptance Criteria:**
- AC1: I can submit a position with: title, department, seniority level (junior / mid / senior / lead / principal), status (open / on-hold / filled / closed), and a raw job description text.
- AC2: Required skills can be optionally provided manually as a structured list; if not provided, they will be populated by AI extraction (US-301).
- AC3: The system returns a unique position ID upon successful creation.
- AC4: Position title must be non-empty; all other fields except required_skills are mandatory.

**Example positions:**
- "Fullstack Engineer — Angular + .NET" (senior)
- "Frontend Engineer — React" (mid)
- "Backend Engineer — Node.js + PostgreSQL" (mid)
- "DevOps Engineer — Azure + Kubernetes" (senior)

---

### US-202 · Update a Position

**As a** recruiter,  
**I want to** update a position's details or status,  
**so that** the talent bank reflects current hiring needs.

**Acceptance Criteria:**
- AC1: I can update any field, including marking it as filled or closed.
- AC2: A timestamp is recorded on every update.

---

### US-203 · List Open Positions

**As a** recruiter,  
**I want to** see all currently open positions,  
**so that** I can manage my hiring pipeline.

**Acceptance Criteria:**
- AC1: Default view shows only positions with status = "open".
- AC2: I can optionally filter by seniority level or department.
- AC3: Results show: title, seniority, department, number of required skills, and date created.
- AC4: Results are paginated (default 20 per page).

---

## E3 — AI Skill Extraction

### US-301 · Extract Skills from a Job Description

**As a** recruiter,  
**I want to** paste a job description and have the AI extract the required skills,  
**so that** I don't have to manually catalogue every skill for every position.

**Acceptance Criteria:**
- AC1: I provide a raw JD text (free-form, any length); the system returns a structured list of required skills.
- AC2: Each extracted skill includes: skill name, category, whether it is required or preferred, and the AI's confidence (high / medium / low).
- AC3: The AI also returns a brief summary of the role (2–3 sentences) and suggested seniority level.
- AC4: Extraction is powered by a LangGraph agent that uses Claude; the agent must handle ambiguous or poorly-written JDs gracefully.
- AC5: The extraction result can be applied to an existing position (updating its required_skills field) or returned standalone.
- AC6: The agent must identify software-engineering-specific skills: frameworks, languages, platforms, methodologies (e.g., Angular, React, .NET, Node.js, Java, Azure, AWS, Docker, Kubernetes, Agile, REST APIs).

**LangGraph Agent Nodes for this flow:**
1. `parse_jd` — clean and chunk the raw text
2. `extract_skills` — Claude call to extract structured skills
3. `classify_skills` — categorize and assign confidence
4. `generate_summary` — Claude call to produce role summary + seniority suggestion
5. `validate_output` — schema validation, retry if malformed

---

### US-302 · Re-extract Skills for a Position

**As a** recruiter,  
**I want to** trigger re-extraction of skills for an existing position after editing the JD,  
**so that** the required skills stay in sync with the latest description.

**Acceptance Criteria:**
- AC1: I can trigger re-extraction for any position by its ID.
- AC2: The previous required_skills are replaced (not appended) by the new extraction result.
- AC3: A history entry is stored so I can see what the skills were before re-extraction.

---

## E4 — Profile Recommendation

### US-401 · Recommend Candidates for a Position

**As a** recruiter,  
**I want to** ask the system to recommend the best-matching candidates for an open position,  
**so that** I can focus my outreach on the strongest matches.

**Acceptance Criteria:**
- AC1: I provide a position ID; the system returns a ranked list of candidate profiles.
- AC2: Each recommendation includes: candidate name, match score (0–100), matched skills, missing skills, and a short AI-generated rationale.
- AC3: The ranking considers: percentage of required skills matched, proficiency alignment (expert > advanced > intermediate > beginner), years of experience vs. seniority level.
- AC4: At least the top 5 candidates are returned (or all if fewer than 5 exist).
- AC5: The recommendation is powered by a LangGraph multi-agent graph that reasons over candidates rather than doing a simple SQL query.
- AC6: Results clearly distinguish between "required skill matched", "preferred skill matched", and "skill missing".

**LangGraph Agent Nodes for this flow:**
1. `load_position` — fetch position and its required skills
2. `fetch_candidates` — retrieve all candidates from the talent bank
3. `score_candidates` — compute structured skill match scores
4. `rank_and_filter` — sort by score, apply seniority filter
5. `generate_rationale` — Claude call to write a human-readable justification per top candidate
6. `compile_report` — assemble final ranked recommendation list

---

### US-402 · Recommend Positions for a Candidate

**As a** recruiter or candidate,  
**I want to** see which open positions best match a given candidate's profile,  
**so that** I can identify the right opportunities for them.

**Acceptance Criteria:**
- AC1: I provide a candidate ID; the system returns a ranked list of open positions.
- AC2: Each result includes: position title, match score, skills the candidate covers, skills the candidate is missing, and a short rationale.
- AC3: Only positions with status = "open" are included.

---

## E5 — Skill Gap Analysis

### US-501 · Analyze Skill Gap for a Candidate vs. a Position

**As a** recruiter or candidate,  
**I want to** see a detailed skill gap analysis between a specific candidate and a specific position,  
**so that** I can understand what training or experience is needed.

**Acceptance Criteria:**
- AC1: I provide a candidate ID and a position ID; the system returns a structured gap analysis.
- AC2: The analysis groups skills into three buckets: "Fully Matches" (candidate has skill at required or higher proficiency), "Partial Match" (candidate has skill but below required proficiency), and "Missing" (candidate does not have the skill at all).
- AC3: The AI generates a development recommendation for each missing or partial skill (e.g., "3–6 months of hands-on Angular project experience recommended").
- AC4: The analysis includes an overall suitability verdict: "Strong Match", "Moderate Match", "Weak Match", or "Not Suitable".
- AC5: The LangGraph agent must use structured reasoning — it should not hallucinate skill requirements not present in the position.

**LangGraph Agent Nodes for this flow:**
1. `load_pair` — fetch candidate profile and position requirements
2. `compare_skills` — deterministic diff: matched / partial / missing
3. `assess_seniority_fit` — check years of experience vs. seniority level
4. `generate_gap_report` — Claude call to produce recommendations
5. `produce_verdict` — determine suitability label

---

### US-502 · Batch Gap Analysis for a Position

**As a** recruiter,  
**I want to** run a skill gap analysis for all candidates recommended for a position at once,  
**so that** I can compare gaps across the shortlist.

**Acceptance Criteria:**
- AC1: I provide a position ID; the system runs gap analysis for the top N recommended candidates (N configurable, default 5).
- AC2: Results are returned as a comparative table showing each candidate's gap bucket counts.

---

## E6 — Recruiter Dashboard (UI)

### US-601 · Dashboard — Talent Bank Overview

**As a** recruiter,  
**I want a** dashboard showing the talent bank at a glance,  
**so that** I can see the size, skill distribution, and recent additions.

**Acceptance Criteria:**
- AC1: Dashboard shows total candidate count, breakdown by top skills, and breakdown by seniority.
- AC2: Recent profiles (last 10 added) are visible.

---

### US-602 · Dashboard — Position Pipeline View

**As a** recruiter,  
**I want to** see all positions and their status in a pipeline view,  
**so that** I can manage my hiring funnel.

**Acceptance Criteria:**
- AC1: Positions are grouped by status (open / on-hold / filled / closed).
- AC2: Clicking a position shows its required skills and allows triggering recommendation.

---

### US-603 · Dashboard — AI Extraction Interface

**As a** recruiter,  
**I want a** text input where I can paste a job description and immediately see the AI-extracted skills,  
**so that** I can validate the extraction before applying it to a position.

**Acceptance Criteria:**
- AC1: Input accepts multi-line text.
- AC2: Extracted skills are shown in a structured table with name, category, required/preferred, and confidence.
- AC3: I can edit individual extracted skills before saving them to a position.

---

### US-604 · Dashboard — Recommendation View

**As a** recruiter,  
**I want to** trigger a recommendation from the position detail page and see ranked candidates,  
**so that** I can immediately act on AI recommendations.

**Acceptance Criteria:**
- AC1: A "Find Candidates" button on the position page triggers US-401.
- AC2: Results are shown as ranked cards with match score, matched skills highlighted, and the AI rationale visible on expand.
- AC3: I can click through to any recommended candidate's full profile.

---

## Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR-01 | AI extraction (US-301) must complete within 15 seconds for JDs up to 2,000 words |
| NFR-02 | Recommendation (US-401) must complete within 20 seconds for a talent bank up to 500 candidates |
| NFR-03 | All API endpoints must return JSON responses with consistent error shapes |
| NFR-04 | The system must not expose raw LLM prompts in API responses |
| NFR-05 | All Claude calls must use prompt caching where the system prompt is static |
| NFR-06 | LangGraph graphs must be observable — each node transition must be logged with timing |
| NFR-07 | The PostgreSQL schema must use migrations (Alembic) for reproducibility |
| NFR-08 | API must include OpenAPI/Swagger documentation auto-generated by FastAPI |
