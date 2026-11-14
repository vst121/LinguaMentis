"""Response Proposition domain entity.

Represents an agent-crafted, elevated German rewrite of the learner's response,
aligned with their original meaning and active Hat mode, together with
structured highlights explaining specific lexical and syntactic upgrades.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class PropositionHighlight:
    """A single highlighted upgrade inside ``ResponseProposition.improved_response``."""

    upgraded_phrase: str
    original_phrase: str
    explanation: str
    category: str


@dataclass(slots=True)
class ResponseProposition:
    """Elevated German response proposition aligned with a learner's turn response."""

    id: UUID
    turn_id: UUID
    improved_response: str
    highlights: list[PropositionHighlight] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
