"""Spoken conversation orchestration service."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from uuid import UUID

from linguamentis.agents.registry import AgentRegistry
from linguamentis.ai.gateway import AIGateway
from linguamentis.application.mindquests.service import MindQuestService
from linguamentis.domain.evaluations.german import GermanEvaluation
from linguamentis.domain.evaluations.thinking import ThinkingEvaluation
from linguamentis.domain.hats.types import HatType
from linguamentis.domain.mindquests.entities import MindQuest, Turn
from linguamentis.domain.mindquests.enums import MindQuestStatus
from linguamentis.shared.exceptions import DomainError


@dataclass(slots=True)
class ConversationOpeningResult:
    mindquest: MindQuest
    active_hat: HatType | None
    active_turn: Turn | None
    spoken_text: str
    audio_base64: str
    audio_mime_type: str
    is_completed: bool


@dataclass(slots=True)
class ConversationTurnResult:
    mindquest: MindQuest
    user_transcript: str
    spoken_reply: str
    audio_base64: str
    audio_mime_type: str
    thinking_evaluation: ThinkingEvaluation
    german_evaluation: GermanEvaluation
    active_hat: HatType | None
    active_turn: Turn | None
    transitioned_hat: HatType | None
    is_completed: bool


class ConversationService:
    def __init__(
        self,
        *,
        mindquest_service: MindQuestService,
        agent_registry: AgentRegistry,
        gateway: AIGateway,
    ) -> None:
        self._mq = mindquest_service
        self._registry = agent_registry
        self._gateway = gateway

    async def open_conversation(self, mindquest_id: UUID) -> ConversationOpeningResult:
        mq = await self._mq.get_mindquest(mindquest_id)
        if mq.status == MindQuestStatus.COMPLETED:
            return ConversationOpeningResult(
                mq, None, None, "Diese MindQuest ist abgeschlossen.", "", "audio/wav", True
            )

        if mq.status == MindQuestStatus.TOPIC_SELECTED:
            started = await self._mq.start_mindquest(mindquest_id)
            mq, turn = started.mindquest, started.initial_turn
        else:
            r = mq.current_hat_round
            turn = r.latest_turn if r else None

        if mq.current_hat is None or turn is None:
            raise DomainError("Kein aktiver Gesprächsschritt gefunden.")

        is_first = len(mq.completed_hats) == 0 and turn.turn_number == 1
        agent = self._registry.conversation
        text = agent.build_opening_utterance(
            hat=mq.current_hat,
            topic=mq.topic,
            challenge_question=turn.challenge_question,
            is_first_turn_overall=is_first,
        )
        speech = await agent.synthesize_safe(text)
        return ConversationOpeningResult(
            mq, mq.current_hat, turn, text, speech.audio_base64, speech.mime_type, False
        )

    async def process_turn(
        self,
        mindquest_id: UUID,
        *,
        transcript: str | None = None,
        audio_base64: str | None = None,
        mime_type: str = "audio/webm",
        include_audio: bool = True,
    ) -> ConversationTurnResult:
        user_text = (transcript or "").strip()
        if not user_text:
            if not audio_base64:
                raise DomainError("Weder Transkript noch Sprachaufnahme übergeben.")
            try:
                decoded = base64.b64decode(audio_base64, validate=True)
            except Exception as exc:
                raise DomainError("Ungültige Audio-Daten.") from exc
            if not decoded:
                raise DomainError("Leere Sprachaufnahme.")
            mime = mime_type.split(";")[0].strip().lower() or "audio/webm"
            stt = await self._gateway.transcribe_german_speech(
                audio_base64=audio_base64, mime_type=mime
            )
            user_text = stt.text.strip()

        if not user_text:
            raise DomainError("Keine gesprochene Antwort erkannt.")

        mq_before = await self._mq.get_mindquest(mindquest_id)
        prev_hat = mq_before.current_hat or HatType.WHITE
        sub = await self._mq.submit_response(mindquest_id=mindquest_id, user_response=user_text)

        transitioned: HatType | None = None
        done = False
        if sub.round_should_complete:
            adv = await self._mq.advance_mindquest(mindquest_id)
            updated_mq = adv.mindquest
            done = adv.is_completed
            transitioned = adv.next_hat
            turn = adv.initial_turn
            next_q = turn.challenge_question if turn else None
        else:
            updated_mq = await self._mq.get_mindquest(mindquest_id)
            r = updated_mq.current_hat_round
            turn = r.latest_turn if r else None
            next_q = sub.next_challenge.question if sub.next_challenge else None

        agent = self._registry.conversation
        reply = await agent.compose_turn_reply(
            topic=updated_mq.topic,
            target_level=updated_mq.target_level.value,
            previous_hat=prev_hat,
            user_response=user_text,
            thinking_feedback=sub.feedback.thinking_feedback,
            german_feedback=sub.feedback.german_feedback,
            transitioned_hat=transitioned,
            next_question=next_q,
            is_completed=done,
        )
        if include_audio:
            speech = await agent.synthesize_safe(reply.spoken_reply)
            audio_b64, audio_mime = speech.audio_base64, speech.mime_type
        else:
            audio_b64, audio_mime = "", "audio/wav"

        return ConversationTurnResult(
            updated_mq,
            user_text,
            reply.spoken_reply,
            audio_b64,
            audio_mime,
            sub.thinking_evaluation,
            sub.german_evaluation,
            updated_mq.current_hat,
            turn,
            transitioned,
            done,
        )
