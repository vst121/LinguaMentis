"""Optional Jev decision layer; Jev can recommend, but never owns app state."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol
import httpx

@dataclass(frozen=True, slots=True)
class JevDecision:
    choice: str
    confidence: float
    probabilities: dict[str, float]

class DecisionVerifier(Protocol):
    async def evaluate_hat_adherence(self, *, hat: str, challenge: str, response: str) -> JevDecision: ...

class DisabledDecisionVerifier:
    async def evaluate_hat_adherence(self, *, hat: str, challenge: str, response: str) -> JevDecision:
        return JevDecision("review", 0.0, {})

class JevClient:
    def __init__(self, *, api_key: str, base_url: str, timeout: float = 10.0) -> None:
        self._api_key, self._base_url, self._timeout = api_key, base_url.rstrip("/"), timeout

    async def evaluate_hat_adherence(self, *, hat: str, challenge: str, response: str) -> JevDecision:
        payload: dict[str, Any] = {
            "model": "typesafe/jev-1.13",
            "state": {"hat": hat, "challenge": challenge, "response": response},
            "questions": [{"id": "hat_adherence", "type": "choice",
                "options": ["adherent", "not_adherent", "review"],
                "question": "Does the response follow the assigned Six Thinking Hat?"}],
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            result = await client.post(f"{self._base_url}/alpha/decisions",
                headers={"Authorization": f"Bearer {self._api_key}"}, json=payload)
            result.raise_for_status()
            body = result.json()
        answer = body.get("answers", body.get("results", [body]))[0]
        return JevDecision(str(answer.get("choice", "review")), float(answer.get("confidence", 0.0)),
                           {str(k): float(v) for k, v in answer.get("probabilities", {}).items()})
