"""Learning application service.

Per Architecture.md #29: UserLearningProfile is derived from accumulated
evaluations and evidence across historical MindQuests.
"""

from __future__ import annotations

from uuid import UUID

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
        user_quests = await self._mindquest_repo.list_by_user(user_id, limit=200)
        completed_quests = [q for q in user_quests if q.status.value == "COMPLETED"]

        # Collect all evaluations across user's mindquests
        all_thinking = []
        all_german = []
        for quest in user_quests:
            t_evals = await self._evaluation_repo.list_thinking_evaluations_by_mindquest(
                quest.id
            )
            g_evals = await self._evaluation_repo.list_german_evaluations_by_mindquest(
                quest.id
            )
            all_thinking.extend(t_evals)
            all_german.extend(g_evals)

        thinking_overall = (
            sum(e.score for e in all_thinking) / len(all_thinking) if all_thinking else None
        )
        german_overall = (
            sum(e.score for e in all_german) / len(all_german) if all_german else None
        )

        # Dimension breakdown
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

        return UserLearningProfile(
            user_id=user_id,
            mindquests_completed=len(completed_quests),
            thinking_overall=round(thinking_overall, 1) if thinking_overall else None,
            german_overall=round(german_overall, 1) if german_overall else None,
            thinking_dimensions=tuple(thinking_dimension_scores),
            german_dimensions=tuple(german_dimension_scores),
            strongest_thinking_dimension=strongest_t,
            weakest_thinking_dimension=weakest_t,
            strongest_german_dimension=strongest_g,
            weakest_german_dimension=weakest_g,
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
        res.append(DimensionScore(name=name, score=avg))
    return res
