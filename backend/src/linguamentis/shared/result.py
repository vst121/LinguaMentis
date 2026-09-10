"""A tiny Result type used across application services.

The domain and application layers prefer explicit success/failure values over
exceptions for *expected* failure modes (e.g. invalid state transitions).
Exceptions remain reserved for truly exceptional situations
(see :mod:`linguamentis.shared.exceptions`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar

T = TypeVar("T")
E = TypeVar("E")


@dataclass(frozen=True, slots=True)
class Result[T, E]:
    """Represents either a successful value or an error value, never both."""

    _value: T | None
    _error: E | None
    is_ok: bool

    @classmethod
    def ok(cls, value: T) -> Result[T, E]:
        return cls(_value=value, _error=None, is_ok=True)

    @classmethod
    def err(cls, error: E) -> Result[T, E]:
        return cls(_value=None, _error=error, is_ok=False)

    @property
    def is_err(self) -> bool:
        return not self.is_ok

    def unwrap(self) -> T:
        if not self.is_ok:
            raise ValueError(f"Called unwrap() on an error Result: {self._error!r}")
        assert self._value is not None or self.is_ok
        return self._value  # type: ignore[return-value]

    def unwrap_err(self) -> E:
        if self.is_ok:
            raise ValueError("Called unwrap_err() on an ok Result")
        return self._error  # type: ignore[return-value]

    def map(self, fn):  # noqa: ANN001, ANN201
        if self.is_ok:
            return Result.ok(fn(self._value))
        return Result.err(self._error)
