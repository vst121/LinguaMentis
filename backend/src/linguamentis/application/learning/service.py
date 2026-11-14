"""Learning application service.

Per Architecture.md #29: UserLearningProfile is derived from accumulated
evaluations and evidence across historical MindQuests.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from linguamentis.domain.evaluations.german import GermanEvaluation
from linguamentis.domain.evaluations.thinking import ThinkingEvaluation
from linguamentis.domain.learning.profile import UserLearningProfile
from linguamentis.domain.users.value_objects import DimensionScore
from linguamentis.infrastructure.database.repositories.activity_repository import (
    UserActivity,
    UserActivityRepository,
)
from linguamentis.infrastructure.database.repositories.evaluation_repository import (
    EvaluationRepository,
)
from linguamentis.infrastructure.database.repositories.mindquest_repository import (
    MindQuestRepository,
)


@dataclass(frozen=True, slots=True)
class EvaluationMetricsSummary:
    thinking_overall: float | None
    german_overall: float | None
    thinking_dimensions: tuple[DimensionScore, ...]
    german_dimensions: tuple[DimensionScore, ...]
    strongest_thinking_dimension: str | None
    weakest_thinking_dimension: str | None
    strongest_german_dimension: str | None
    weakest_german_dimension: str | None


def aggregate_evaluation_metrics(
    all_thinking: list[ThinkingEvaluation],
    all_german: list[GermanEvaluation],
) -> EvaluationMetricsSummary:
    thinking_overall = (
        sum(e.score for e in all_thinking) / len(all_thinking) if all_thinking else None
    )
    german_overall = (
        sum(e.score for e in all_german) / len(all_german) if all_german else None
    )

    t_dims = [
        ("hat_adherence", [e.hat_adherence for e in all_thinking]),
        ("relevance", [e.relevance for e in all_thinking]),
        ("reasoning", [e.reasoning for e in all_thinking]),
        ("depth", [e.depth for e in all_thinking]),
        ("specificity", [e.specificity for e in all_thinking]),
    ]
    g_dims = [
        ("grammar", [e.grammar for e in all_german]),
        ("vocabulary", [e.vocabulary for e in all_german]),
        ("sentence_structure", [e.sentence_structure for e in all_german]),
        ("naturalness", [e.naturalness for e in all_german]),
        ("level_appropriateness", [e.level_appropriateness for e in all_german]),
    ]

    thinking_dimension_scores = _calc_dimension_scores(t_dims)
    german_dimension_scores = _calc_dimension_scores(g_dims)

    strongest_t = (
        max(thinking_dimension_scores, key=lambda d: d.score).name
        if thinking_dimension_scores
        else None
    )
    weakest_t = (
        min(thinking_dimension_scores, key=lambda d: d.score).name
        if thinking_dimension_scores
        else None
    )

    strongest_g = (
        max(german_dimension_scores, key=lambda d: d.score).name
        if german_dimension_scores
        else None
    )
    weakest_g = (
        min(german_dimension_scores, key=lambda d: d.score).name
        if german_dimension_scores
        else None
    )

    return EvaluationMetricsSummary(
        thinking_overall=round(thinking_overall, 1) if thinking_overall is not None else None,
        german_overall=round(german_overall, 1) if german_overall is not None else None,
        thinking_dimensions=tuple(thinking_dimension_scores),
        german_dimensions=tuple(german_dimension_scores),
        strongest_thinking_dimension=strongest_t,
        weakest_thinking_dimension=weakest_t,
        strongest_german_dimension=strongest_g,
        weakest_german_dimension=weakest_g,
    )


class LearningService:
    def __init__(
        self,
        mindquest_repo: MindQuestRepository,
        evaluation_repo: EvaluationRepository,
        activity_repo: UserActivityRepository,
    ) -> None:
        self._mindquest_repo = mindquest_repo
        self._evaluation_repo = evaluation_repo
        self._activity_repo = activity_repo

    async def get_user_learning_profile(self, user_id: UUID) -> UserLearningProfile:
        completed_count = await self._mindquest_repo.count_completed_by_user(user_id)
        all_thinking = await self._evaluation_repo.list_thinking_evaluations_by_user(user_id)
        all_german = await self._evaluation_repo.list_german_evaluations_by_user(user_id)
        metrics = aggregate_evaluation_metrics(all_thinking, all_german)

        return UserLearningProfile(
            user_id=user_id,
            mindquests_completed=completed_count,
            thinking_overall=metrics.thinking_overall,
            german_overall=metrics.german_overall,
            thinking_dimensions=metrics.thinking_dimensions,
            german_dimensions=metrics.german_dimensions,
            strongest_thinking_dimension=metrics.strongest_thinking_dimension,
            weakest_thinking_dimension=metrics.weakest_thinking_dimension,
            strongest_german_dimension=metrics.strongest_german_dimension,
            weakest_german_dimension=metrics.weakest_german_dimension,
        )

    async def list_user_activities(
        self, user_id: UUID, limit: int = 50, offset: int = 0
    ) -> list[UserActivity]:
        return await self._activity_repo.list_by_user(user_id, limit=limit, offset=offset)


def _calc_dimension_scores(dims: list[tuple[str, list[int]]]) -> list[DimensionScore]:
    res: list[DimensionScore] = []
    for name, vals in dims:
        if not vals:
            continue
        avg = round(sum(vals) / len(vals), 1)
        res.append(DimensionScore(name=name, score=avg, sample_size=len(vals)))        
    return res
