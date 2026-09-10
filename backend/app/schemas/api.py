import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field, field_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SkillCategory(str, Enum):
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


class Proficiency(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"
    expert = "expert"


class Seniority(str, Enum):
    junior = "junior"
    mid = "mid"
    senior = "senior"
    lead = "lead"
    principal = "principal"


class PositionStatus(str, Enum):
    open = "open"
    on_hold = "on_hold"
    filled = "filled"
    closed = "closed"


class Confidence(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


# ---------------------------------------------------------------------------
# Candidate Skill schemas
# ---------------------------------------------------------------------------

class CandidateSkillCreate(BaseModel):
    skill_name: str = Field(..., min_length=1, max_length=255)
    category: SkillCategory
    proficiency: Proficiency
    years_used: int | None = Field(None, ge=0, le=50)


class CandidateSkillRead(BaseModel):
    id: uuid.UUID
    skill_name: str
    category: SkillCategory
    proficiency: Proficiency
    years_used: int | None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Candidate schemas
# ---------------------------------------------------------------------------

class CandidateCreate(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    years_of_experience: int = Field(..., ge=0, le=50)
    current_role_title: str = Field(..., min_length=1, max_length=255)
    summary: str | None = None
    skills: list[CandidateSkillCreate] = Field(default_factory=list)


class CandidateUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=255)
    email: EmailStr | None = None
    years_of_experience: int | None = Field(None, ge=0, le=50)
    current_role_title: str | None = Field(None, min_length=1, max_length=255)
    summary: str | None = None
    skills: list[CandidateSkillCreate] | None = None


class CandidateRead(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str
    years_of_experience: int
    current_role_title: str
    summary: str | None
    skills: list[CandidateSkillRead]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CandidateListRead(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str
    years_of_experience: int
    current_role_title: str
    skills: list[CandidateSkillRead]

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Position Skill schemas
# ---------------------------------------------------------------------------

class PositionSkillCreate(BaseModel):
    skill_name: str = Field(..., min_length=1, max_length=255)
    category: SkillCategory
    is_required: bool = True
    min_proficiency: Proficiency
    confidence: Confidence = Confidence.high
    source: str = Field("manual", max_length=50)

    @field_validator("source")
    @classmethod
    def source_must_be_valid(cls, v: str) -> str:
        allowed = {"manual", "ai_extracted"}
        if v not in allowed:
            raise ValueError(f"source must be one of {allowed}")
        return v


class PositionSkillRead(BaseModel):
    id: uuid.UUID
    skill_name: str
    category: SkillCategory
    is_required: bool
    min_proficiency: Proficiency
    confidence: Confidence
    source: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Position schemas
# ---------------------------------------------------------------------------

class PositionCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    department: str = Field(..., min_length=1, max_length=255)
    seniority: Seniority
    status: PositionStatus = PositionStatus.open
    description_raw: str = Field(..., min_length=1)
    required_skills: list[PositionSkillCreate] = Field(default_factory=list)


class PositionUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    department: str | None = Field(None, min_length=1, max_length=255)
    seniority: Seniority | None = None
    status: PositionStatus | None = None
    description_raw: str | None = None
    required_skills: list[PositionSkillCreate] | None = None


class PositionRead(BaseModel):
    id: uuid.UUID
    title: str
    department: str
    seniority: Seniority
    status: PositionStatus
    description_raw: str
    ai_summary: str | None
    ai_seniority_suggestion: str | None
    required_skills: list[PositionSkillRead]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PositionListRead(BaseModel):
    id: uuid.UUID
    title: str
    department: str
    seniority: Seniority
    status: PositionStatus
    required_skills: list[PositionSkillRead]
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Skill Extraction schemas
# ---------------------------------------------------------------------------

class SkillExtractionRequest(BaseModel):
    jd_text: str = Field(..., min_length=10, description="Raw job description text")


class ExtractedSkillItem(BaseModel):
    skill_name: str
    category: SkillCategory
    is_required: bool
    min_proficiency: Proficiency
    confidence: Confidence


class SkillExtractionResponse(BaseModel):
    skills: list[ExtractedSkillItem]
    summary: str
    suggested_seniority: str
    trace: list[dict]


# ---------------------------------------------------------------------------
# Recommendation schemas
# ---------------------------------------------------------------------------

class CandidateRecommendationRead(BaseModel):
    candidate_id: uuid.UUID
    candidate_name: str
    current_role_title: str
    years_of_experience: int
    match_score: float
    matched_skills: list[str]
    missing_skills: list[str]
    partial_skills: list[str]
    rationale: str
    suitability_verdict: str


class PositionRecommendationRead(BaseModel):
    position_id: uuid.UUID
    position_title: str
    department: str
    seniority: Seniority
    match_score: float
    matched_skills: list[str]
    missing_skills: list[str]
    partial_skills: list[str]
    rationale: str
    suitability_verdict: str


# ---------------------------------------------------------------------------
# Gap Analysis schemas
# ---------------------------------------------------------------------------

class GapAnalysisRequest(BaseModel):
    candidate_id: uuid.UUID
    position_id: uuid.UUID


class SkillGapItem(BaseModel):
    skill_name: str
    min_proficiency: str
    is_required: bool
    candidate_proficiency: str | None = None


class GapAnalysisResponse(BaseModel):
    candidate_id: uuid.UUID
    candidate_name: str
    position_id: uuid.UUID
    position_title: str
    score: float
    verdict: str
    seniority_fit: bool
    seniority_note: str
    fully_matched: list[SkillGapItem]
    partial: list[SkillGapItem]
    missing: list[SkillGapItem]
    recommendations: list[str]
    trace: list[dict]


class BatchGapAnalysisResponse(BaseModel):
    position_id: uuid.UUID
    position_title: str
    results: list[GapAnalysisResponse]
