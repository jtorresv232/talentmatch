import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SkillCategory(str, enum.Enum):
    frontend = "frontend"
    backend = "backend"
    cloud = "cloud"
    devops = "devops"
    database = "database"
    mobile = "mobile"
    testing = "testing"
    architecture = "architecture"
    soft_skill = "soft_skill"
    other = "other"


class Proficiency(str, enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"
    expert = "expert"


PROFICIENCY_ORDER = {
    Proficiency.beginner: 1,
    Proficiency.intermediate: 2,
    Proficiency.advanced: 3,
    Proficiency.expert: 4,
}


class Seniority(str, enum.Enum):
    junior = "junior"
    mid = "mid"
    senior = "senior"
    lead = "lead"
    principal = "principal"


class PositionStatus(str, enum.Enum):
    open = "open"
    on_hold = "on_hold"
    filled = "filled"
    closed = "closed"


class Confidence(str, enum.Enum):
    high = "high"
    medium = "medium"
    low = "low"


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    years_of_experience: Mapped[int] = mapped_column(Integer, nullable=False)
    current_role_title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    skills: Mapped[list["CandidateSkill"]] = relationship("CandidateSkill", back_populates="candidate", cascade="all, delete-orphan")
    recommendation_results: Mapped[list["RecommendationResult"]] = relationship("RecommendationResult", back_populates="candidate", cascade="all, delete-orphan")


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    skill_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[SkillCategory] = mapped_column(Enum(SkillCategory), nullable=False)
    proficiency: Mapped[Proficiency] = mapped_column(Enum(Proficiency), nullable=False)
    years_used: Mapped[int | None] = mapped_column(Integer, nullable=True)

    candidate: Mapped["Candidate"] = relationship("Candidate", back_populates="skills")


class Position(Base):
    __tablename__ = "positions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[str] = mapped_column(String(255), nullable=False)
    seniority: Mapped[Seniority] = mapped_column(Enum(Seniority), nullable=False)
    status: Mapped[PositionStatus] = mapped_column(Enum(PositionStatus), nullable=False, default=PositionStatus.open)
    description_raw: Mapped[str] = mapped_column(Text, nullable=False)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_seniority_suggestion: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    required_skills: Mapped[list["PositionSkill"]] = relationship("PositionSkill", back_populates="position", cascade="all, delete-orphan")
    extraction_history: Mapped[list["ExtractionHistory"]] = relationship("ExtractionHistory", back_populates="position", cascade="all, delete-orphan")
    recommendation_results: Mapped[list["RecommendationResult"]] = relationship("RecommendationResult", back_populates="position", cascade="all, delete-orphan")


class PositionSkill(Base):
    __tablename__ = "position_skills"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    position_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("positions.id", ondelete="CASCADE"), nullable=False)
    skill_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[SkillCategory] = mapped_column(Enum(SkillCategory), nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    min_proficiency: Mapped[Proficiency] = mapped_column(Enum(Proficiency), nullable=False)
    confidence: Mapped[Confidence] = mapped_column(Enum(Confidence), nullable=False, default=Confidence.high)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="manual")

    position: Mapped["Position"] = relationship("Position", back_populates="required_skills")


class ExtractionHistory(Base):
    __tablename__ = "extraction_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    position_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("positions.id", ondelete="CASCADE"), nullable=False)
    extracted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    skills_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    agent_trace: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    position: Mapped["Position"] = relationship("Position", back_populates="extraction_history")


class RecommendationResult(Base):
    __tablename__ = "recommendation_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    position_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("positions.id", ondelete="CASCADE"), nullable=False)
    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    match_score: Mapped[float] = mapped_column(Float, nullable=False)
    matched_skills: Mapped[dict] = mapped_column(JSON, nullable=False)
    missing_skills: Mapped[dict] = mapped_column(JSON, nullable=False)
    partial_skills: Mapped[dict] = mapped_column(JSON, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    suitability_verdict: Mapped[str] = mapped_column(String(50), nullable=False)

    position: Mapped["Position"] = relationship("Position", back_populates="recommendation_results")
    candidate: Mapped["Candidate"] = relationship("Candidate", back_populates="recommendation_results")
