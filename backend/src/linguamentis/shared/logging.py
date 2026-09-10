"""Structured logging configuration.

Per Architecture.md #46 (Observability), logs should carry structured fields
such as ``request_id``, ``mindquest_id``, ``turn_id``, ``hat``, ``model``,
``operation`` and ``latency`` — and must avoid logging sensitive or
unnecessary user content (e.g. full German responses, prompts).
"""

from __future__ import annotations

import logging
import sys

import structlog


def configure_logging(level: str = "INFO") -> None:
    """Configure structlog + stdlib logging once, at process startup."""

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper(), logging.INFO),
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)


# Fields that must never be logged verbatim (per Architecture.md #45/#46).
SENSITIVE_FIELDS = frozenset({"response_text", "prompt", "system_prompt", "user_response"})
