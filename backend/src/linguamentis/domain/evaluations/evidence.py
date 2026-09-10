"""Evidence — a first-class domain concept (Architecture.md #21).

"An evaluation should not only contain `Score = 78`. It should explain why."

Evidence and Correction are shared between the Thinking and German
evaluation domains, and between the domain layer and the AI structured
output contracts (``ai/models.py`` mirrors these shapes for LLM parsing;
the application layer converts AI-layer models into these domain
dataclasses so the domain stays independent of the AI schema library).
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Evidence:
    """Explains why a particular score/dimension was assigned."""

    dimension: str
    observation: str
    impact: str


@dataclass(frozen=True, slots=True)
class Correction:
    """A selective, high-value German correction (Architecture.md / Rubric #23).

    Corrections should be selective — not every sentence is rewritten.
    Priority: repeated mistakes > meaningful mistakes > B2/C1-relevant
    mistakes > clarity-affecting errors > high-value naturalness upgrades.
    """

    original: str
    corrected: str
    explanation: str
    category: str


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    """A persisted Evidence item, linked back to the turn/evaluation it
    belongs to, used for the user's learning history (Architecture.md #21)."""

    id: UUID
    turn_id: UUID
    evaluation_kind: str  # "thinking" | "german"
    evidence: Evidence
