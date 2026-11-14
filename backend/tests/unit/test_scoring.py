"""Unit tests for Thinking & German score formulas and score anchors."""

from uuid import uuid4

import pytest

from linguamentis.domain.evaluations.german import GermanEvaluation, compute_german_score
from linguamentis.domain.evaluations.thinking import (
    ThinkingEvaluation,
    compute_thinking_score,
)


def test_compute_thinking_score_calculation():
    # Weights: hat_adherence 0.25, relevance 0.15, reasoning 0.25, depth 0.20, specificity 0.15
    score = compute_thinking_score(
        hat_adherence=100,
        relevance=100,
        reasoning=100,
        depth=100,
        specificity=100,
    )
    assert score == 100

    score_partial = compute_thinking_score(
        hat_adherence=80,
        relevance=80,
        reasoning=80,
        depth=80,
        specificity=80,
    )
    assert score_partial == 80

    # Weighted calculation: 100*0.25 + 60*0.15 + 80*0.25 + 70*0.20 + 50*0.15 = 75.5 -> 76
    weighted = compute_thinking_score(
        hat_adherence=100,
        relevance=60,
        reasoning=80,
        depth=70,
        specificity=50,
    )
    assert weighted == 76


def test_compute_german_score_calculation():
    # Weights: grammar 0.25, vocabulary 0.20, sentence_structure 0.20,
    # naturalness 0.20, level_appropriateness 0.15
    score = compute_german_score(
        grammar=90,
        vocabulary=90,
        sentence_structure=90,
        naturalness=90,
        level_appropriateness=90,
    )
    assert score == 90


@pytest.mark.parametrize(
    "invalid_kwargs",
    [
        {"hat_adherence": 105, "relevance": 80, "reasoning": 80, "depth": 80, "specificity": 80},
        {"hat_adherence": 80, "relevance": -1, "reasoning": 80, "depth": 80, "specificity": 80},
        {"hat_adherence": 80, "relevance": 80, "reasoning": 101, "depth": 80, "specificity": 80},
        {"hat_adherence": 80, "relevance": 80, "reasoning": 80, "depth": -5, "specificity": 80},
        {"hat_adherence": 80, "relevance": 80, "reasoning": 80, "depth": 80, "specificity": 200},
    ],
)
def test_thinking_score_out_of_range_raises(invalid_kwargs):
    with pytest.raises(ValueError):
        compute_thinking_score(**invalid_kwargs)


@pytest.mark.parametrize(
    "invalid_kwargs",
    [
        {
            "grammar": -1,
            "vocabulary": 80,
            "sentence_structure": 80,
            "naturalness": 80,
            "level_appropriateness": 80,
        },
        {
            "grammar": 80,
            "vocabulary": 101,
            "sentence_structure": 80,
            "naturalness": 80,
            "level_appropriateness": 80,
        },
    ],
)
def test_german_score_out_of_range_raises(invalid_kwargs):
    with pytest.raises(ValueError):
        compute_german_score(**invalid_kwargs)


@pytest.mark.parametrize(
    ("uniform_val", "expected_thinking_anchor", "expected_german_anchor"),
    [
        (95, "Exceptional thinking for the task", "Excellent command for the target level"),
        (85, "Strong", "Strong"),
        (75, "Good", "Good"),
        (65, "Adequate", "Adequate"),
        (55, "Weak", "Weak"),
        (35, "Very weak", "Very weak"),
        (20, "Insufficient", "Insufficient"),
    ],
)
def test_thinking_and_german_score_anchors(
    uniform_val: int, expected_thinking_anchor: str, expected_german_anchor: str
):
    t_eval = ThinkingEvaluation(
        id=uuid4(),
        turn_id=uuid4(),
        hat_adherence=uniform_val,
        relevance=uniform_val,
        reasoning=uniform_val,
        depth=uniform_val,
        specificity=uniform_val,
    )
    g_eval = GermanEvaluation(
        id=uuid4(),
        turn_id=uuid4(),
        grammar=uniform_val,
        vocabulary=uniform_val,
        sentence_structure=uniform_val,
        naturalness=uniform_val,
        level_appropriateness=uniform_val,
    )
    assert t_eval.score == uniform_val
    assert t_eval.score_anchor() == expected_thinking_anchor
    assert g_eval.score == uniform_val
    assert g_eval.score_anchor() == expected_german_anchor

