"""SQLAlchemy 2.x ORM models.

Per Architecture.md #26/#27: PostgreSQL is the V1 persistence layer, mapped
with async SQLAlchemy. These are intentionally kept in ``infrastructure``,
separate from the plain-dataclass domain entities in ``domain/``; the
repositories in ``infrastructure/database/repositories`` translate between
the two.

Tables (Architecture.md #26):
    users, mind_quests, hat_rounds, turns, thinking_evaluations,
    german_evaluations, evidence, user_activities, final_reflections
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    target_level: Mapped[str] = mapped_column(String(2), nullable=False, default="B2")
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    mindquests: Mapped[list["MindQuestModel"]] = relationship(back_populates="user")
    activities: Mapped[list["UserActivityModel"]] = relationship(back_populates="user")


class MindQuestModel(Base):
    __tablename__ = "mind_quests"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    topic: Mapped[str] = mapped_column(Text, nullable=False, default="")
    target_level: Mapped[str] = mapped_column(String(2), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="CREATED")
    current_hat: Mapped[str | None] = mapped_column(String(10), nullable=True)
    planned_hats: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    user: Mapped["UserModel"] = relationship(back_populates="mindquests")
    hat_rounds: Mapped[list["HatRoundModel"]] = relationship(
        back_populates="mindquest", order_by="HatRoundModel.sequence_index", cascade="all, delete-orphan"
    )
    final_reflection: Mapped["FinalReflectionModel | None"] = relationship(
        back_populates="mindquest", uselist=False, cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_mind_quests_user_id", "user_id"),)


class HatRoundModel(Base):
    __tablename__ = "hat_rounds"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mindquest_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("mind_quests.id"), nullable=False
    )
    hat: Mapped[str] = mapped_column(String(10), nullable=False)
    sequence_index: Mapped[int] = mapped_column(nullable=False)
    started_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    mindquest: Mapped["MindQuestModel"] = relationship(back_populates="hat_rounds")
    turns: Mapped[list["TurnModel"]] = relationship(
        back_populates="hat_round", order_by="TurnModel.turn_number", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_hat_rounds_mindquest_id", "mindquest_id"),)


class TurnModel(Base):
    __tablename__ = "turns"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hat_round_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("hat_rounds.id"), nullable=False
    )
    turn_number: Mapped[int] = mapped_column(nullable=False)
    hat: Mapped[str] = mapped_column(String(10), nullable=False)
    challenge_question: Mapped[str] = mapped_column(Text, nullable=False)
    challenge_instruction: Mapped[str] = mapped_column(Text, nullable=False, default="")
    difficulty: Mapped[int] = mapped_column(nullable=False, default=1)
    user_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    responded_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    hat_round: Mapped["HatRoundModel"] = relationship(back_populates="turns")
    thinking_evaluation: Mapped["ThinkingEvaluationModel | None"] = relationship(
        back_populates="turn", uselist=False, cascade="all, delete-orphan"
    )
    german_evaluation: Mapped["GermanEvaluationModel | None"] = relationship(
        back_populates="turn", uselist=False, cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_turns_hat_round_id", "hat_round_id"),)


class ThinkingEvaluationModel(Base):
    __tablename__ = "thinking_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    turn_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("turns.id"), nullable=False, unique=True
    )
    hat_adherence: Mapped[int] = mapped_column(nullable=False)
    relevance: Mapped[int] = mapped_column(nullable=False)
    reasoning: Mapped[int] = mapped_column(nullable=False)
    depth: Mapped[int] = mapped_column(nullable=False)
    specificity: Mapped[int] = mapped_column(nullable=False)
    strengths: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    weaknesses: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    recommendations: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    turn: Mapped["TurnModel"] = relationship(back_populates="thinking_evaluation")
    evidence: Mapped[list["EvidenceModel"]] = relationship(
        back_populates="thinking_evaluation",
        cascade="all, delete-orphan",
        foreign_keys="EvidenceModel.thinking_evaluation_id",
    )


class GermanEvaluationModel(Base):
    __tablename__ = "german_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    turn_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("turns.id"), nullable=False, unique=True
    )
    grammar: Mapped[int] = mapped_column(nullable=False)
    vocabulary: Mapped[int] = mapped_column(nullable=False)
    sentence_structure: Mapped[int] = mapped_column(nullable=False)
    naturalness: Mapped[int] = mapped_column(nullable=False)
    level_appropriateness: Mapped[int] = mapped_column(nullable=False)
    corrections: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    strengths: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    weaknesses: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    recommendations: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    turn: Mapped["TurnModel"] = relationship(back_populates="german_evaluation")
    evidence: Mapped[list["EvidenceModel"]] = relationship(
        back_populates="german_evaluation",
        cascade="all, delete-orphan",
        foreign_keys="EvidenceModel.german_evaluation_id",
    )


class EvidenceModel(Base):
    """Evidence is first-class and persisted, per Architecture.md #21."""

    __tablename__ = "evidence"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thinking_evaluation_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("thinking_evaluations.id"), nullable=True
    )
    german_evaluation_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("german_evaluations.id"), nullable=True
    )
    dimension: Mapped[str] = mapped_column(String(80), nullable=False)
    observation: Mapped[str] = mapped_column(Text, nullable=False)
    impact: Mapped[str] = mapped_column(Text, nullable=False)

    thinking_evaluation: Mapped["ThinkingEvaluationModel | None"] = relationship(
        back_populates="evidence", foreign_keys=[thinking_evaluation_id]
    )
    german_evaluation: Mapped["GermanEvaluationModel | None"] = relationship(
        back_populates="evidence", foreign_keys=[german_evaluation_id]
    )


class FinalReflectionModel(Base):
    __tablename__ = "final_reflections"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mindquest_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("mind_quests.id"), nullable=False, unique=True
    )
    thinking_summary: Mapped[str] = mapped_column(Text, nullable=False)
    german_summary: Mapped[str] = mapped_column(Text, nullable=False)
    thinking_section: Mapped[dict] = mapped_column(JSON, nullable=False)
    german_section: Mapped[dict] = mapped_column(JSON, nullable=False)
    closing_message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    mindquest: Mapped["MindQuestModel"] = relationship(back_populates="final_reflection")


class UserActivityModel(Base):
    """Chronological journey log. NOT authoritative state (Architecture.md #30)."""

    __tablename__ = "user_activities"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    mindquest_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("mind_quests.id"), nullable=True
    )
    activity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    user: Mapped["UserModel"] = relationship(back_populates="activities")

    __table_args__ = (Index("ix_user_activities_user_id_created_at", "user_id", "created_at"),)
