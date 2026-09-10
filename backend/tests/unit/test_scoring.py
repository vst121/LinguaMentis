"""Unit tests for Thinking & German score formulas."""

import pytest

from linguamentis.domain.evaluations.german import compute_german_score
from linguamentis.domain.evaluations.thinking import compute_thinking_score


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


def test_compute_german_score_calculation():
    # Weights: grammar 0.25, vocabulary 0.20, sentence_structure 0.20, naturalness 0.20, level_appropriateness 0.15
    score = compute_german_score(
        grammar=90,
        vocabulary=90,
        sentence_structure=90,
        naturalness=90,
        level_appropriateness=90,
    )
    assert score == 90


def test_score_out_of_range_raises():
    with pytest.raises(ValueError):
        compute_thinking_score(
            hat_adherence=105,
            relevance=80,
            reasoning=80,
            depth=80,
            specificity=80,
        )
