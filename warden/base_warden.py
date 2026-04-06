"""Abstract base class for all Warden implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class WardenResult:
    detected: bool          # True = attack detected
    confidence: str         # "high" / "medium" / "low"
    reason: str             # human-readable explanation
    warden_type: str        # "rule_based" / "llm_based"


class BaseWarden(ABC):
    @abstractmethod
    def inspect(self, reasoning_trace: str, final_answer: str, original_prompt: str) -> WardenResult:
        """
        Inspect the model's reasoning trace and final answer.

        Args:
            reasoning_trace: The CoT surrogate text (REASONING section).
            final_answer:    The model's final answer (ANSWER section).
            original_prompt: The original user prompt (for alignment checking).

        Returns:
            WardenResult with detection decision.
        """
        ...
