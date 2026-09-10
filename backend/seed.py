"""
Seed script — populates 10 candidates and 5 positions.
Run from the backend/ directory:  python seed.py
"""
import asyncio
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.models.db import (
    Candidate,
    CandidateSkill,
    Confidence,
    Position,
    PositionSkill,
    PositionStatus,
    Proficiency,
    Seniority,
    SkillCategory,
)

# ---------------------------------------------------------------------------
# Candidate data
# ---------------------------------------------------------------------------

CANDIDATES = [
    {
        "full_name": "Carlos Mendoza",
        "email": "carlos.mendoza@example.com",
        "years_of_experience": 7,
        "current_role_title": "Senior Fullstack Developer",
        "summary": "Experienced Angular and .NET developer with strong enterprise background.",
        "skills": [
            ("Angular", SkillCategory.frontend, Proficiency.expert, 6),
            (".NET", SkillCategory.backend, Proficiency.advanced, 5),
            ("C#", SkillCategory.backend, Proficiency.advanced, 5),
            ("SQL Server", SkillCategory.database, Proficiency.intermediate, 4),
            ("Azure", SkillCategory.cloud, Proficiency.intermediate, 2),
            ("TypeScript", SkillCategory.frontend, Proficiency.advanced, 4),
        ],
    },
    {
        "full_name": "Priya Sharma",
        "email": "priya.sharma@example.com",
        "years_of_experience": 4,
        "current_role_title": "Frontend Developer",
        "summary": "React specialist focused on performance and accessible UI.",
        "skills": [
            ("React", SkillCategory.frontend, Proficiency.advanced, 4),
            ("TypeScript", SkillCategory.frontend, Proficiency.advanced, 3),
            ("Redux", SkillCategory.frontend, Proficiency.intermediate, 3),
            ("CSS", SkillCategory.frontend, Proficiency.advanced, 4),
            ("Jest", SkillCategory.testing, Proficiency.intermediate, 2),
        ],
    },
    {
        "full_name": "James Okafor",
        "email": "james.okafor@example.com",
        "years_of_experience": 6,
        "current_role_title": "Senior Backend Engineer",
        "summary": "Node.js and microservices expert with deep API design experience.",
        "skills": [
            ("Node.js", SkillCategory.backend, Proficiency.expert, 6),
            ("TypeScript", SkillCategory.frontend, Proficiency.advanced, 4),
            ("PostgreSQL", SkillCategory.database, Proficiency.advanced, 5),
            ("Docker", SkillCategory.devops, Proficiency.intermediate, 3),
            ("AWS", SkillCategory.cloud, Proficiency.intermediate, 2),
            ("REST API", SkillCategory.backend, Proficiency.expert, 6),
        ],
    },
    {
        "full_name": "Mei Lin",
        "email": "mei.lin@example.com",
        "years_of_experience": 9,
        "current_role_title": "Lead Java Engineer",
        "summary": "Java architect with extensive Spring Boot and distributed systems experience.",
        "skills": [
            ("Java", SkillCategory.backend, Proficiency.expert, 9),
            ("Spring Boot", SkillCategory.backend, Proficiency.expert, 7),
            ("Kafka", SkillCategory.backend, Proficiency.advanced, 4),
            ("PostgreSQL", SkillCategory.database, Proficiency.advanced, 6),
            ("Kubernetes", SkillCategory.devops, Proficiency.intermediate, 3),
            ("Microservices", SkillCategory.architecture, Proficiency.expert, 5),
        ],
    },
    {
        "full_name": "Rafael Torres",
        "email": "rafael.torres@example.com",
        "years_of_experience": 5,
        "current_role_title": "DevOps Engineer",
        "summary": "CI/CD and infrastructure automation specialist with cloud-native focus.",
        "skills": [
            ("Kubernetes", SkillCategory.devops, Proficiency.advanced, 4),
            ("Docker", SkillCategory.devops, Proficiency.expert, 5),
            ("Terraform", SkillCategory.devops, Proficiency.advanced, 3),
            ("AWS", SkillCategory.cloud, Proficiency.advanced, 4),
            ("GitHub Actions", SkillCategory.devops, Proficiency.advanced, 3),
            ("Linux", SkillCategory.devops, Proficiency.expert, 5),
        ],
    },
    {
        "full_name": "Sofia Reyes",
        "email": "sofia.reyes@example.com",
        "years_of_experience": 2,
        "current_role_title": "Junior Frontend Developer",
        "summary": "React developer early in career, strong with modern hooks and component patterns.",
        "skills": [
            ("React", SkillCategory.frontend, Proficiency.intermediate, 2),
            ("JavaScript", SkillCategory.frontend, Proficiency.intermediate, 2),
            ("CSS", SkillCategory.frontend, Proficiency.intermediate, 2),
            ("Git", SkillCategory.devops, Proficiency.beginner, 2),
        ],
    },
    {
        "full_name": "David Kim",
        "email": "david.kim@example.com",
        "years_of_experience": 4,
        "current_role_title": "Angular Developer",
        "summary": "Mid-level Angular developer transitioning into fullstack with .NET.",
        "skills": [
            ("Angular", SkillCategory.frontend, Proficiency.advanced, 4),
            ("TypeScript", SkillCategory.frontend, Proficiency.intermediate, 3),
            ("RxJS", SkillCategory.frontend, Proficiency.intermediate, 3),
            ("C#", SkillCategory.backend, Proficiency.beginner, 1),
            (".NET", SkillCategory.backend, Proficiency.beginner, 1),
        ],
    },
    {
        "full_name": "Anna Kowalski",
        "email": "anna.kowalski@example.com",
        "years_of_experience": 5,
        "current_role_title": ".NET Backend Developer",
        "summary": "Solid .NET and C# developer with SQL Server expertise.",
        "skills": [
            (".NET", SkillCategory.backend, Proficiency.advanced, 5),
            ("C#", SkillCategory.backend, Proficiency.advanced, 5),
            ("SQL Server", SkillCategory.database, Proficiency.advanced, 4),
            ("Azure", SkillCategory.cloud, Proficiency.intermediate, 2),
            ("REST API", SkillCategory.backend, Proficiency.advanced, 4),
        ],
    },
    {
        "full_name": "Liam Chen",
        "email": "liam.chen@example.com",
        "years_of_experience": 3,
        "current_role_title": "Backend Developer",
        "summary": "Node.js backend developer comfortable with REST and GraphQL.",
        "skills": [
            ("Node.js", SkillCategory.backend, Proficiency.intermediate, 3),
            ("GraphQL", SkillCategory.backend, Proficiency.intermediate, 2),
            ("PostgreSQL", SkillCategory.database, Proficiency.intermediate, 2),
            ("Docker", SkillCategory.devops, Proficiency.beginner, 1),
            ("JavaScript", SkillCategory.frontend, Proficiency.advanced, 3),
        ],
    },
    {
        "full_name": "Fatima Al-Hassan",
        "email": "fatima.alhassan@example.com",
        "years_of_experience": 6,
        "current_role_title": "Fullstack Engineer",
        "summary": "Versatile fullstack engineer with React frontend and Node.js backend skills.",
        "skills": [
            ("React", SkillCategory.frontend, Proficiency.advanced, 5),
            ("Node.js", SkillCategory.backend, Proficiency.advanced, 5),
            ("TypeScript", SkillCategory.frontend, Proficiency.advanced, 4),
            ("PostgreSQL", SkillCategory.database, Proficiency.intermediate, 3),
            ("Docker", SkillCategory.devops, Proficiency.intermediate, 2),
            ("AWS", SkillCategory.cloud, Proficiency.beginner, 1),
        ],
    },
]

# ---------------------------------------------------------------------------
# Position data
# ---------------------------------------------------------------------------

POSITIONS = [
    {
        "title": "Senior Angular / .NET Fullstack Engineer",
        "department": "Product Engineering",
        "seniority": Seniority.senior,
        "status": PositionStatus.open,
        "description_raw": (
            "We are seeking a Senior Fullstack Engineer to build enterprise-grade web applications. "
            "You will work across the Angular frontend and .NET backend, designing scalable REST APIs "
            "and delivering high-quality TypeScript components. Azure cloud experience is a plus."
        ),
        "skills": [
            ("Angular", SkillCategory.frontend, True, Proficiency.advanced, Confidence.high),
            (".NET", SkillCategory.backend, True, Proficiency.advanced, Confidence.high),
            ("C#", SkillCategory.backend, True, Proficiency.intermediate, Confidence.high),
            ("TypeScript", SkillCategory.frontend, True, Proficiency.intermediate, Confidence.high),
            ("SQL Server", SkillCategory.database, False, Proficiency.intermediate, Confidence.medium),
            ("Azure", SkillCategory.cloud, False, Proficiency.beginner, Confidence.medium),
        ],
    },
    {
        "title": "Senior React Frontend Developer",
        "department": "Digital Experience",
        "seniority": Seniority.senior,
        "status": PositionStatus.open,
        "description_raw": (
            "Join our Digital Experience team to craft performant, accessible React applications. "
            "You must have strong TypeScript skills and experience with state management (Redux or Zustand). "
            "Testing discipline (Jest, React Testing Library) is required."
        ),
        "skills": [
            ("React", SkillCategory.frontend, True, Proficiency.advanced, Confidence.high),
            ("TypeScript", SkillCategory.frontend, True, Proficiency.advanced, Confidence.high),
            ("Redux", SkillCategory.frontend, True, Proficiency.intermediate, Confidence.high),
            ("Jest", SkillCategory.testing, True, Proficiency.intermediate, Confidence.high),
            ("CSS", SkillCategory.frontend, False, Proficiency.intermediate, Confidence.medium),
        ],
    },
    {
        "title": "Mid-Level Node.js Backend Engineer",
        "department": "Platform Engineering",
        "seniority": Seniority.mid,
        "status": PositionStatus.open,
        "description_raw": (
            "We need a Backend Engineer to build and maintain our Node.js microservices. "
            "Strong PostgreSQL and REST API design skills are essential. "
            "Docker and basic cloud (AWS) exposure expected."
        ),
        "skills": [
            ("Node.js", SkillCategory.backend, True, Proficiency.intermediate, Confidence.high),
            ("PostgreSQL", SkillCategory.database, True, Proficiency.intermediate, Confidence.high),
            ("REST API", SkillCategory.backend, True, Proficiency.intermediate, Confidence.high),
            ("Docker", SkillCategory.devops, False, Proficiency.beginner, Confidence.medium),
            ("AWS", SkillCategory.cloud, False, Proficiency.beginner, Confidence.low),
        ],
    },
    {
        "title": "Lead Java / Spring Boot Engineer",
        "department": "Core Services",
        "seniority": Seniority.lead,
        "status": PositionStatus.open,
        "description_raw": (
            "Lead the design and implementation of our core services platform using Java and Spring Boot. "
            "Experience with Kafka, microservices architecture, and Kubernetes required. "
            "You will mentor junior engineers and drive technical decisions."
        ),
        "skills": [
            ("Java", SkillCategory.backend, True, Proficiency.expert, Confidence.high),
            ("Spring Boot", SkillCategory.backend, True, Proficiency.advanced, Confidence.high),
            ("Kafka", SkillCategory.backend, True, Proficiency.intermediate, Confidence.high),
            ("Microservices", SkillCategory.architecture, True, Proficiency.advanced, Confidence.high),
            ("Kubernetes", SkillCategory.devops, False, Proficiency.intermediate, Confidence.medium),
            ("PostgreSQL", SkillCategory.database, False, Proficiency.intermediate, Confidence.medium),
        ],
    },
    {
        "title": "Senior DevOps / Platform Engineer",
        "department": "Infrastructure",
        "seniority": Seniority.senior,
        "status": PositionStatus.open,
        "description_raw": (
            "Own our cloud infrastructure and CI/CD pipelines. "
            "You will design and maintain Kubernetes clusters, Terraform modules, and GitHub Actions workflows. "
            "Deep AWS experience and Linux administration skills are required. Docker is a must."
        ),
        "skills": [
            ("Kubernetes", SkillCategory.devops, True, Proficiency.advanced, Confidence.high),
            ("Docker", SkillCategory.devops, True, Proficiency.advanced, Confidence.high),
            ("Terraform", SkillCategory.devops, True, Proficiency.intermediate, Confidence.high),
            ("AWS", SkillCategory.cloud, True, Proficiency.advanced, Confidence.high),
            ("Linux", SkillCategory.devops, True, Proficiency.advanced, Confidence.high),
            ("GitHub Actions", SkillCategory.devops, False, Proficiency.intermediate, Confidence.medium),
        ],
    },
]


# ---------------------------------------------------------------------------
# Seed runner
# ---------------------------------------------------------------------------

async def seed() -> None:
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as db:
        existing = await db.execute(text("SELECT COUNT(*) FROM candidates"))
        count = existing.scalar()
        if count > 0:
            print(f"Database already has {count} candidates. Skipping seed.")
            print("To re-seed, truncate the tables first.")
            await engine.dispose()
            return

        print("Seeding candidates...")
        for c_data in CANDIDATES:
            candidate = Candidate(
                full_name=c_data["full_name"],
                email=c_data["email"],
                years_of_experience=c_data["years_of_experience"],
                current_role_title=c_data["current_role_title"],
                summary=c_data["summary"],
            )
            db.add(candidate)
            await db.flush()

            for skill_name, category, proficiency, years_used in c_data["skills"]:
                db.add(CandidateSkill(
                    candidate_id=candidate.id,
                    skill_name=skill_name,
                    category=category,
                    proficiency=proficiency,
                    years_used=years_used,
                ))

            print(f"  + {candidate.full_name}")

        print("Seeding positions...")
        for p_data in POSITIONS:
            position = Position(
                title=p_data["title"],
                department=p_data["department"],
                seniority=p_data["seniority"],
                status=p_data["status"],
                description_raw=p_data["description_raw"],
            )
            db.add(position)
            await db.flush()

            for skill_name, category, is_required, min_proficiency, confidence in p_data["skills"]:
                db.add(PositionSkill(
                    position_id=position.id,
                    skill_name=skill_name,
                    category=category,
                    is_required=is_required,
                    min_proficiency=min_proficiency,
                    confidence=confidence,
                    source="manual",
                ))

            print(f"  + {position.title}")

        await db.commit()
        print("Seed complete.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
