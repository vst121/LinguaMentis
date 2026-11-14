"""ConversationAgent — Spoken German dialogue partner across Six Thinking Hats."""

from __future__ import annotations

from linguamentis.ai.gateway import AIGateway
from linguamentis.ai.models import ConversationReplyOutput, SynthesizedSpeech
from linguamentis.domain.hats.types import HatType
from linguamentis.shared.logging import get_logger

logger = get_logger(__name__)

HAT_SPOKEN_LABELS: dict[HatType, str] = {
    HatType.WHITE: "den Weißen Hut für Fakten und belegbare Informationen",
    HatType.YELLOW: "den Gelben Hut für Chancen und positive Potenziale",
    HatType.GREEN: "den Grünen Hut für kreative Ideen und Alternativen",
    HatType.RED: "den Roten Hut für dein Bauchgefühl und deine Emotionen",
    HatType.BLACK: "den Schwarzen Hut für Risiken und kritische Einwände",
    HatType.BLUE: "den Blauen Hut für die Synthese und deine Schlussfolgerung",
}


class ConversationAgent:
    """Conducts natural spoken German conversations while respecting Hat boundaries."""

    def __init__(self, gateway: AIGateway) -> None:
        self._gateway = gateway

    def build_opening_utterance(
        self,
        *,
        hat: HatType,
        topic: str,
        challenge_question: str,
        is_first_turn_overall: bool,
    ) -> str:
        hat_label = HAT_SPOKEN_LABELS[hat]
        if is_first_turn_overall:
            return (
                f"Willkommen zu unserem Gespräch über das Thema: {topic}. "
                f"Wir starten mit dem Blick auf {hat_label}. "
                f"{challenge_question}"
            )
        return f"Wir betrachten jetzt {hat_label}. {challenge_question}"

    async def compose_turn_reply(
        self,
        *,
        topic: str,
        target_level: str,
        previous_hat: HatType,
        user_response: str,
        thinking_feedback: str,
        german_feedback: str,
        transitioned_hat: HatType | None,
        next_question: str | None,
        is_completed: bool,
    ) -> ConversationReplyOutput:
        transitioned_label = (
            HAT_SPOKEN_LABELS[transitioned_hat] if transitioned_hat else None
        )
        return await self._gateway.generate_conversation_reply(
            topic=topic,
            target_level=target_level,
            previous_hat=previous_hat.value,
            user_response=user_response,
            thinking_feedback=thinking_feedback,
            german_feedback=german_feedback,
            transitioned_hat=transitioned_label,
            next_question=next_question,
            is_completed=is_completed,
        )

    async def synthesize_safe(self, text: str) -> SynthesizedSpeech:
        """Synthesize German TTS audio; degrade gracefully to empty audio on TTS failure."""
        try:
            return await self._gateway.synthesize_german_speech(text=text)
        except Exception as exc:
            logger.warning("agent.conversation.tts_degraded", error=str(exc))
            return SynthesizedSpeech(audio_base64="", mime_type="audio/wav")
