"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-09-09

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "candidates",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("years_of_experience", sa.Integer(), nullable=False),
        sa.Column("current_role_title", sa.String(255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "positions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("department", sa.String(255), nullable=False),
        sa.Column(
            "seniority",
            sa.Enum("junior", "mid", "senior", "lead", "principal", name="seniority"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("open", "on_hold", "filled", "closed", name="positionstatus"),
            nullable=False,
        ),
        sa.Column("description_raw", sa.Text(), nullable=False),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("ai_seniority_suggestion", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "candidate_skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_name", sa.String(255), nullable=False),
        sa.Column(
            "category",
            sa.Enum("frontend", "backend", "cloud", "devops", "database", "mobile", "testing", "architecture", "soft_skill", "other", name="skillcategory"),
            nullable=False,
        ),
        sa.Column(
            "proficiency",
            sa.Enum("beginner", "intermediate", "advanced", "expert", name="proficiency"),
            nullable=False,
        ),
        sa.Column("years_used", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "position_skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_name", sa.String(255), nullable=False),
        sa.Column(
            "category",
            sa.Enum("frontend", "backend", "cloud", "devops", "database", "mobile", "testing", "architecture", "soft_skill", "other", name="skillcategory"),
            nullable=False,
        ),
        sa.Column("is_required", sa.Boolean(), nullable=False),
        sa.Column(
            "min_proficiency",
            sa.Enum("beginner", "intermediate", "advanced", "expert", name="proficiency"),
            nullable=False,
        ),
        sa.Column(
            "confidence",
            sa.Enum("high", "medium", "low", name="confidence"),
            nullable=False,
        ),
        sa.Column("source", sa.String(50), nullable=False),
        sa.ForeignKeyConstraint(["position_id"], ["positions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "extraction_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("extracted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("skills_snapshot", postgresql.JSON(), nullable=False),
        sa.Column("agent_trace", postgresql.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["position_id"], ["positions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "recommendation_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("match_score", sa.Float(), nullable=False),
        sa.Column("matched_skills", postgresql.JSON(), nullable=False),
        sa.Column("missing_skills", postgresql.JSON(), nullable=False),
        sa.Column("partial_skills", postgresql.JSON(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("suitability_verdict", sa.String(50), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["position_id"], ["positions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("recommendation_results")
    op.drop_table("extraction_history")
    op.drop_table("position_skills")
    op.drop_table("candidate_skills")
    op.drop_table("positions")
    op.drop_table("candidates")

    op.execute("DROP TYPE IF EXISTS confidence")
    op.execute("DROP TYPE IF EXISTS proficiency")
    op.execute("DROP TYPE IF EXISTS skillcategory")
    op.execute("DROP TYPE IF EXISTS positionstatus")
    op.execute("DROP TYPE IF EXISTS seniority")
