"""User domain entity.

Per Architecture.md #28: authentication is out of scope for V1. A `User`
entity still exists so that all user-owned data references a `UserId`,
giving a clean path toward multi-user support later without redesigning
the domain.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from linguamentis.domain.mindquests.enums import LanguageLevel


@dataclass(slots=True)
class User:
    id: UUID
    display_name: str
    target_level: LanguageLevel = LanguageLevel.B2
    created_at: datetime = field(default_factory=datetime.utcnow)
