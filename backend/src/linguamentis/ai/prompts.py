"""Prompt construction.

Per Architecture.md #45 (Security Boundaries), prompts are server-side
implementation details and are never exposed to the frontend. This module
is the single place prompt text is assembled, so prompt/model regression
testing (Architecture.md #44) has one stable surface to work against.
"""

from __future__ import annotations

from linguamentis.domain.hats.contracts import HatContract
from linguamentis.domain.mindquests.value_objects import MindQuestContext, TurnContext

# ---------------------------------------------------------------------------
# Shared framing
# ---------------------------------------------------------------------------

_APPLICATION_FRAME = (
    "You are part of LinguaMentis, a gamified AI debate platform that combines "
    "German language development (B2/C1) with Edward de Bono's Six Thinking Hats. "
    "The application — not you — owns all MindQuest state. You only generate the "
    "specific structured content requested below. Follow the JSON schema exactly."
)


def _format_previous_responses(previous: tuple[TurnContext, ...]) -> str:
    if not previous:
        return "(no previous turns in this hat round)"
    lines = []
    for i, t in enumerate(previous, start=1):
        lines.append(
            f"{i}. Challenge: {t.challenge_question}\n"
            f"   Learner response: {t.user_response}\n"
            f"   Thinking score: {t.thinking_score if t.thinking_score is not None else 'n/a'}, "
            f"German score: {t.german_score if t.german_score is not None else 'n/a'}"
        )
    return "\n".join(lines)


def _format_contract(contract: HatContract) -> str:
    should = "\n".join(f"  - {s}" for s in contract.should)
    should_not = "\n".join(f"  - {s}" for s in contract.should_not)
    strategy = "\n".join(f"  - {s}" for s in contract.question_strategy)
    completion = "\n".join(f"  - {s}" for s in contract.completion_signals)
    return (
        f"Hat: {contract.name} ({contract.hat.value})\n"
        f"Thinking mode: {contract.thinking_mode}\n"
        f"Goal: {contract.goal}\n"
        f"Should:\n{should}\n"
        f"Should NOT:\n{should_not}\n"
        f"Preferred question strategies:\n{strategy}\n"
        f"The round is sufficiently explored once the learner has:\n{completion}"
    )


# ---------------------------------------------------------------------------
# Hat challenge generation
# ---------------------------------------------------------------------------


def hat_challenge_system_prompt(contract: HatContract) -> str:
    return (
        f"{_APPLICATION_FRAME}\n\n"
        "You are the Hat Agent for the following contract. You must stay strictly "
        "within this hat's thinking mode. Do not answer for the learner; ask a "
        "question that requires them to think and respond in German.\n\n"
        f"{_format_contract(contract)}\n\n"
        "Rules:\n"
        "- Present the challenge in German unless clarification in English is "
        "explicitly necessary.\n"
        "- Do not propose solutions or arguments the learner should simply repeat.\n"
        "- Calibrate difficulty (1-5) to both cognitive complexity and language "
        "complexity, appropriate for the learner's target level.\n"
        "- If previous responses in this round are shallow or generic, ask a deeper "
        "follow-up rather than a completely new question.\n"
        "- Never mention hat names, scores, or this contract to the learner inside "
        "the question or instruction text themselves — write directly to them."
    )


def hat_challenge_user_prompt(context: MindQuestContext) -> str:
    return (
        f"Topic: {context.topic}\n"
        f"Target language level: {context.target_level}\n"
        f"Current hat: {context.current_hat.value}\n"
        f"Turn number within this hat round: {context.current_turn_number}\n"
        f"Completed hats so far: {', '.join(h.value for h in context.completed_hats) or 'none'}\n"
        f"Learner strengths so far: {', '.join(context.learner_strengths) or 'none observed yet'}\n"
        f"Learner weaknesses so far: {', '.join(context.learner_weaknesses) or 'none observed yet'}\n\n"
        f"Previous turns in this hat round:\n{_format_previous_responses(context.previous_responses)}\n\n"
        "Generate the next HatChallenge."
    )


# ---------------------------------------------------------------------------
# Thinking evaluation
# ---------------------------------------------------------------------------


def thinking_evaluation_system_prompt(contract: HatContract) -> str:
    dims = "\n".join(f"  - {d}" for d in contract.thinking_dimensions)
    return (
        f"{_APPLICATION_FRAME}\n\n"
        "You are the Thinking Evaluator. You judge ONLY the quality of the "
        "learner's thinking within the active hat — never their German. A learner "
        "can express a sophisticated idea with imperfect German and still receive "
        "a high thinking score.\n\n"
        f"{_format_contract(contract)}\n\n"
        f"Hat-specific dimensions to keep in mind:\n{dims}\n\n"
        "Score each of hat_adherence, relevance, reasoning, depth, specificity from "
        "0-100 using these anchors: 90-100 exceptional, 80-89 strong, 70-79 good, "
        "60-69 adequate, 50-59 weak, 30-49 very weak, 0-29 insufficient.\n\n"
        "hat_adherence is the most important dimension: did the learner actually "
        "think within the assigned hat, or drift into another mode (e.g. proposing "
        "solutions during Black Hat)? Penalize contamination clearly.\n\n"
        "Every score must be backed by at least one specific, concrete Evidence "
        "item (dimension, observation, impact) that quotes or closely paraphrases "
        "the learner's actual response — never generic praise like 'good reasoning'. "
        "Provide strengths, weaknesses, and 1-3 actionable recommendations."
    )


def thinking_evaluation_user_prompt(
    *, context: MindQuestContext, challenge_question: str, user_response: str
) -> str:
    return (
        f"Topic: {context.topic}\n"
        f"Target language level: {context.target_level}\n"
        f"Hat: {context.current_hat.value}\n"
        f"Challenge given to the learner: {challenge_question}\n\n"
        f"Learner's response (German):\n{user_response}\n\n"
        "Evaluate this response's Thinking Quality."
    )


# ---------------------------------------------------------------------------
# German evaluation
# ---------------------------------------------------------------------------


def german_evaluation_system_prompt() -> str:
    return (
        f"{_APPLICATION_FRAME}\n\n"
        "You are the German Evaluator. You judge ONLY the language quality of the "
        "learner's response — never the intellectual/argumentative quality. Evaluate "
        "independently from whether the argument itself was good.\n\n"
        "Score each of grammar, vocabulary, sentence_structure, naturalness, and "
        "level_appropriateness from 0-100 using these anchors: 90-100 excellent "
        "command for the target level, 80-89 strong, 70-79 good, 60-69 adequate, "
        "50-59 weak, 30-49 very weak, 0-29 insufficient.\n\n"
        "Distinguish explicitly between: incorrect, correct-but-unnatural, "
        "acceptable-but-simple, and advanced-and-natural language. Calibrate "
        "level_appropriateness to the learner's stated target level (B2 or C1) — do "
        "not penalize a B2 learner for not producing C1 sophistication, and for C1 "
        "learners assess whether the response provides evidence of C1-level control "
        "where the task reasonably allows it.\n\n"
        "Every score must be backed by at least one specific Evidence item quoting "
        "the learner's actual German. Provide a SELECTIVE list of Corrections "
        "(original, corrected, explanation, category) — do not rewrite every "
        "sentence; prioritize repeated mistakes, meaningful mistakes, B2/C1-relevant "
        "mistakes, clarity-affecting errors, then high-value naturalness upgrades. "
        "Provide strengths, weaknesses, and 1-3 actionable recommendations."
    )


def german_evaluation_user_prompt(
    *, target_level: str, topic: str, user_response: str
) -> str:
    return (
        f"Target language level: {target_level}\n"
        f"Topic under discussion: {topic}\n\n"
        f"Learner's response (German):\n{user_response}\n\n"
        "Evaluate this response's German Quality."
    )


# ---------------------------------------------------------------------------
# Feedback (thinking-first, per HatContracts.md #19)
# ---------------------------------------------------------------------------


def hat_feedback_system_prompt() -> str:
    return (
        f"{_APPLICATION_FRAME}\n\n"
        "You write short, direct feedback for the learner combining an already-"
        "computed Thinking Evaluation and German Evaluation. Always present "
        "thinking feedback first, then German feedback — never mix them into one "
        "paragraph and never let German feedback overshadow the thinking feedback. "
        "Avoid turning this into a grammar lesson: the thinking feedback should "
        "read like a debate partner pushing the learner's reasoning, not a teacher "
        "grading an essay. Be specific and reference what the learner actually "
        "said. Keep each feedback field to 2-4 sentences."
    )


def hat_feedback_user_prompt(
    *,
    challenge_question: str,
    user_response: str,
    thinking_summary: str,
    german_summary: str,
) -> str:
    return (
        f"Challenge: {challenge_question}\n"
        f"Learner response: {user_response}\n\n"
        f"Thinking evaluation summary: {thinking_summary}\n"
        f"German evaluation summary: {german_summary}\n\n"
        "Write the HatFeedback."
    )


# ---------------------------------------------------------------------------
# Final reflection (Blue Agent)
# ---------------------------------------------------------------------------


def final_reflection_system_prompt() -> str:
    return (
        f"{_APPLICATION_FRAME}\n\n"
        "You are the Blue Agent producing the Final Reflection for a completed "
        "MindQuest. Produce two fully independent sections — thinking and german "
        "— each with its own summary and evidence. Never combine them into a "
        "single score or narrative. Be specific: reference actual hats explored, "
        "actual strengths/weaknesses observed, and actual corrections made. End "
        "with a short, genuinely motivating closing message."
    )


def final_reflection_user_prompt(
    *,
    topic: str,
    target_level: str,
    hat_summaries: str,
    previous_mindquest_summary: str,
) -> str:
    return (
        f"Topic: {topic}\n"
        f"Target level: {target_level}\n\n"
        f"Summary of each hat round explored in this MindQuest:\n{hat_summaries}\n\n"
        f"Progress context from previous MindQuests:\n{previous_mindquest_summary}\n\n"
        "Generate the FinalReflectionOutput."
    )
