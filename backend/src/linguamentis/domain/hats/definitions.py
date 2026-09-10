"""Convenience re-exports for the hats domain package.

Kept as a separate module (per Architecture.md #5 repository layout,
``domain/hats/definitions.py``) so callers can do
``from linguamentis.domain.hats.definitions import HAT_CONTRACTS`` without
depending on the internal module that actually declares the contract data.
"""

from __future__ import annotations

from linguamentis.domain.hats.contracts import (
    BLACK_HAT_CONTRACT,
    BLUE_HAT_CONTRACT,
    GREEN_HAT_CONTRACT,
    HAT_CONTRACTS,
    RED_HAT_CONTRACT,
    WHITE_HAT_CONTRACT,
    YELLOW_HAT_CONTRACT,
    HatContract,
    get_hat_contract,
)
from linguamentis.domain.hats.types import DEFAULT_HAT_SEQUENCE, HatType

__all__ = [
    "HatContract",
    "HatType",
    "HAT_CONTRACTS",
    "DEFAULT_HAT_SEQUENCE",
    "get_hat_contract",
    "WHITE_HAT_CONTRACT",
    "RED_HAT_CONTRACT",
    "BLACK_HAT_CONTRACT",
    "YELLOW_HAT_CONTRACT",
    "GREEN_HAT_CONTRACT",
    "BLUE_HAT_CONTRACT",
]
