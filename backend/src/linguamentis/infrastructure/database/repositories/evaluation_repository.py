"""Evaluation repository implementation and interface.

Per Architecture.md #18/#21/#26: Saves and retrieves Thinking evaluations,
German evaluations, Evidence records, and Final reflections.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from linguamentis.domain.evaluations.evidence import Correction, Evidence, EvidenceRecord
from linguamentis.domain.evaluations.german import GermanEvaluation
from linguamentis.domain.evaluations.thinking import ThinkingEvaluation
from linguamentis.infrastructure.database.models import (
    EvidenceModel,
    FinalReflectionModel,
    GermanEvaluationModel,
    ThinkingEvaluationModel,
)


@dataclass(slots=True)
class FinalReflection:
    id: UUID
    mindquest_id: UUID
    thinking_summary: str
    german_summary: str
    thinking_section: dict
    german_section: dict
    closing_message: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)


class EvaluationRepository(Protocol):
    async def get_thinking_by_turn(self, turn_id: UUID) -> ThinkingEvaluation | None:
        ...

    async def get_german_by_turn(self, turn_id: UUID) -> GermanEvaluation | None:
        ...

    async def save_thinking(self, eval_: ThinkingEvaluation) -> ThinkingEvaluation:
        ...

    async def save_german(self, eval_: GermanEvaluation) -> GermanEvaluation:
        ...

    async def get_final_reflection(self, mindquest_id: UUID) -> FinalReflection | None:
        ...

    async def save_final_reflection(self, reflection: FinalReflection) -> FinalReflection:
        ...

    async def list_evidence_by_user(self, user_id: UUID) -> list[EvidenceRecord]:
        ...

    async def list_thinking_evaluations_by_mindquest(
        self, mindquest_id: UUID
    ) -> list[ThinkingEvaluation]:
        ...

    async def list_german_evaluations_by_mindquest(
        self, mindquest_id: UUID
    ) -> list[GermanEvaluation]:
        ...


class SQLAlchemyEvaluationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_thinking_by_turn(self, turn_id: UUID) -> ThinkingEvaluation | None:
        stmt = (
            select(ThinkingEvaluationModel)
            .where(ThinkingEvaluationModel.turn_id == turn_id)
            .options(selectinload(ThinkingEvaluationModel.evidence))
        )
        res = await self._session.execute(stmt)
        model = res.scalar_one_or_none()
        if model is None:
            return None
        return _to_domain_thinking(model)

    async def get_german_by_turn(self, turn_id: UUID) -> GermanEvaluation | None:
        stmt = (
            select(GermanEvaluationModel)
            .where(GermanEvaluationModel.turn_id == turn_id)
            .options(selectinload(GermanEvaluationModel.evidence))
        )
        res = await self._session.execute(stmt)
        model = res.scalar_one_or_none()
        if model is None:
            return None
        return _to_domain_german(model)

    async def save_thinking(self, eval_: ThinkingEvaluation) -> ThinkingEvaluation:
        stmt = (
            select(ThinkingEvaluationModel)
            .where(ThinkingEvaluationModel.turn_id == eval_.turn_id)
            .options(selectinload(ThinkingEvaluationModel.evidence))
        )
        res = await self._session.execute(stmt)
        model = res.scalar_one_or_none()

        if model is None:
            model = ThinkingEvaluationModel(
                id=eval_.id,
                turn_id=eval_.turn_id,
                hat_adherence=eval_.hat_adherence,
                relevance=eval_.relevance,
                reasoning=eval_.reasoning,
                depth=eval_.depth,
                specificity=eval_.specificity,
                strengths=eval_.strengths,
                weaknesses=eval_.weaknesses,
                recommendations=eval_.recommendations,
                created_at=eval_.created_at,
            )
            self._session.add(model)
        else:
            model.hat_adherence = eval_.hat_adherence
            model.relevance = eval_.relevance
            model.reasoning = eval_.reasoning
            model.depth = eval_.depth
            model.specificity = eval_.specificity
            model.strengths = eval_.strengths
            model.weaknesses = eval_.weaknesses
            model.recommendations = eval_.recommendations

        # Save evidence models
        model.evidence.clear()
        for ev in eval_.evidence:
            ev_model = EvidenceModel(
                id=uuid.uuid4(),
                thinking_evaluation_id=model.id,
                dimension=ev.dimension,
                observation=ev.observation,
                impact=ev.impact,
            )
            model.evidence.append(ev_model)

        await self._session.flush()
        return eval_

    async def save_german(self, eval_: GermanEvaluation) -> GermanEvaluation:
        stmt = (
            select(GermanEvaluationModel)
            .where(GermanEvaluationModel.turn_id == eval_.turn_id)
            .options(selectinload(GermanEvaluationModel.evidence))
        )
        res = await self._session.execute(stmt)
        model = res.scalar_one_or_none()

        corrections_json = [
            {
                "original": c.original,
                "corrected": c.corrected,
                "explanation": c.explanation,
                "category": c.category,
            }
            for c in eval_.corrections
        ]

        if model is None:
            model = GermanEvaluationModel(
                id=eval_.id,
                turn_id=eval_.turn_id,
                grammar=eval_.grammar,
                vocabulary=eval_.vocabulary,
                sentence_structure=eval_.sentence_structure,
                naturalness=eval_.naturalness,
                level_appropriateness=eval_.level_appropriateness,
                corrections=corrections_json,
                strengths=eval_.strengths,
                weaknesses=eval_.weaknesses,
                recommendations=eval_.recommendations,
                created_at=eval_.created_at,
            )
            self._session.add(model)
        else:
            model.grammar = eval_.grammar
            model.vocabulary = eval_.vocabulary
            model.sentence_structure = eval_.sentence_structure
            model.naturalness = eval_.naturalness
            model.level_appropriateness = eval_.level_appropriateness
            model.corrections = corrections_json
            model.strengths = eval_.strengths
            model.weaknesses = eval_.weaknesses
            model.recommendations = eval_.recommendations

        model.evidence.clear()
        for ev in eval_.evidence:
            ev_model = EvidenceModel(
                id=uuid.uuid4(),
                german_evaluation_id=model.id,
                dimension=ev.dimension,
                observation=ev.observation,
                impact=ev.impact,
            )
            model.evidence.append(ev_model)

        await self._session.flush()
        return eval_

    async def get_final_reflection(self, mindquest_id: UUID) -> FinalReflection | None:
        stmt = select(FinalReflectionModel).where(FinalReflectionModel.mindquest_id == mindquest_id)
        res = await self._session.execute(stmt)
        model = res.scalar_one_or_none()
        if model is None:
            return None
        return FinalReflection(
            id=model.id,
            mindquest_id=model.mindquest_id,
            thinking_summary=model.thinking_summary,
            german_summary=model.german_summary,
            thinking_section=model.thinking_section,
            german_section=model.german_section,
            closing_message=model.closing_message,
            created_at=model.created_at,
        )

    async def save_final_reflection(self, reflection: FinalReflection) -> FinalReflection:
        stmt = select(FinalReflectionModel).where(
            FinalReflectionModel.mindquest_id == reflection.mindquest_id
        )
        res = await self._session.execute(stmt)
        model = res.scalar_one_or_none()

        if model is None:
            model = FinalReflectionModel(
                id=reflection.id,
                mindquest_id=reflection.mindquest_id,
                thinking_summary=reflection.thinking_summary,
                german_summary=reflection.german_summary,
                thinking_section=reflection.thinking_section,
                german_section=reflection.german_section,
                closing_message=reflection.closing_message,
                created_at=reflection.created_at,
            )
            self._session.add(model)
        else:
            model.thinking_summary = reflection.thinking_summary
            model.german_summary = reflection.german_summary
            model.thinking_section = reflection.thinking_section
            model.german_section = reflection.german_section
            model.closing_message = reflection.closing_message

        await self._session.flush()
        return reflection

    async def list_evidence_by_user(self, user_id: UUID) -> list[EvidenceRecord]:
        # Fetch all evidence linked via thinking/german evaluations of user's turns
        stmt = (
            select(EvidenceModel)
            .options(
                selectinload(EvidenceModel.thinking_evaluation),
                selectinload(EvidenceModel.german_evaluation),
            )
        )
        res = await self._session.execute(stmt)
        models = res.scalars().all()
        records: list[EvidenceRecord] = []
        for m in models:
            turn_id = None
            kind = "thinking"
            if m.thinking_evaluation:
                turn_id = m.thinking_evaluation.turn_id
                kind = "thinking"
            elif m.german_evaluation:
                turn_id = m.german_evaluation.turn_id
                kind = "german"
            if turn_id is not None:
                records.append(
                    EvidenceRecord(
                        id=m.id,
                        turn_id=turn_id,
                        evaluation_kind=kind,
                        evidence=Evidence(
                            dimension=m.dimension,
                            observation=m.observation,
                            impact=m.impact,
                        ),
                    )
                )
        return records

    async def list_thinking_evaluations_by_mindquest(
        self, mindquest_id: UUID
    ) -> list[ThinkingEvaluation]:
        # Join via turns and hat_rounds
        stmt = (
            select(ThinkingEvaluationModel)
            .join(ThinkingEvaluationModel.turn)
            .join(TurnModel.hat_round)
            .where(HatRoundModel.mindquest_id == mindquest_id)
            .options(selectinload(ThinkingEvaluationModel.evidence))
        )
        res = await self._session.execute(stmt)
        models = res.scalars().all()
        return [_to_domain_thinking(m) for m in models]

    async def list_german_evaluations_by_mindquest(
        self, mindquest_id: UUID
    ) -> list[GermanEvaluation]:
        stmt = (
            select(GermanEvaluationModel)
            .join(GermanEvaluationModel.turn)
            .join(TurnModel.hat_round)
            .where(HatRoundModel.mindquest_id == mindquest_id)
            .options(selectinload(GermanEvaluationModel.evidence))
        )
        res = await self._session.execute(stmt)
        models = res.scalars().all()
        return [_to_domain_german(m) for m in models]


def _to_domain_thinking(model: ThinkingEvaluationModel) -> ThinkingEvaluation:
    evidence = [
        Evidence(dimension=e.dimension, observation=e.observation, impact=e.impact)
        for e in model.evidence
    ]
    return ThinkingEvaluation(
        id=model.id,
        turn_id=model.turn_id,
        hat_adherence=model.hat_adherence,
        relevance=model.relevance,
        reasoning=model.reasoning,
        depth=model.depth,
        specificity=model.specificity,
        evidence=evidence,
        strengths=list(model.strengths or []),
        weaknesses=list(model.weaknesses or []),
        recommendations=list(model.recommendations or []),
        created_at=model.created_at,
    )


def _to_domain_german(model: GermanEvaluationModel) -> GermanEvaluation:
    evidence = [
        Evidence(dimension=e.dimension, observation=e.observation, impact=e.impact)
        for e in model.evidence
    ]
    corrections = [
        Correction(
            original=c.get("original", ""),
            corrected=c.get("corrected", ""),
            explanation=c.get("explanation", ""),
            category=c.get("category", "grammar"),
        )
        for c in (model.corrections or [])
    ]
    return GermanEvaluation(
        id=model.id,
        turn_id=model.turn_id,
        grammar=model.grammar,
        vocabulary=model.vocabulary,
        sentence_structure=model.sentence_structure,
        naturalness=model.naturalness,
        level_appropriateness=model.level_appropriateness,
        evidence=evidence,
        corrections=corrections,
        strengths=list(model.strengths or []),
        weaknesses=list(model.weaknesses or []),
        recommendations=list(model.recommendations or []),
        created_at=model.created_at,
    )
