"""
src/guardrails/output_guardrails.py
=====================================
Guardrail 2 – Output Guardrails
Validates AI-generated responses BEFORE they are shown to the user.

Checks performed:
  • Hallucination / unsupported-claim detection
  • Factual accuracy validation (fitness domain)
  • Toxicity and harmful content filtering
  • Sensitive information filtering
  • Response format validation
"""

from __future__ import annotations

import re
import json
import logging
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger("fitness_buddy")

# ---------------------------------------------------------------------------
# Hallucination / dangerous medical claim patterns
# ---------------------------------------------------------------------------
_DANGEROUS_CLAIM_PATTERNS: List[str] = [
    r"\bcure[sd]?\b.{0,40}\b(cancer|diabetes|hiv|aids|alzheimer)",
    r"\bguaranteed?\s+to\s+(cure|treat|heal|fix)\b",
    r"\bno\s+side\s+effects?\b",
    r"\b100\s*%\s+(safe|effective|guaranteed)\b",
    r"\b(take|use)\s+(?:\d+\s+)?(?:mg|grams?|doses?)\s+of\b",  # dosage instructions
    r"\bstop\s+taking\s+your\s+(medication|medicine|prescription)\b",
    r"\bdon'?t\s+(see|visit|consult)\s+(a\s+)?(doctor|physician|specialist)\b",
    r"\bself[\s-]?medicate\b",
    r"\bclinically\s+proven\b(?!\s+to\s+help\s+with\s+fitness)",
]

_TOXICITY_PATTERNS: List[str] = [
    r"\b(idiot|stupid|moron|dumb|worthless)\b",
    r"\byou\s+are\s+(fat|ugly|gross|disgusting)\b",
    r"\b(kill|harm|hurt)\s+(yourself|your(self)?)\b",
    r"\blose\s+weight\s+or\s+(else|you'll|you\s+will)\b",
    r"\b(nobody|no\s+one)\s+(cares?|likes?)\s+(about\s+)?you\b",
]

_SENSITIVE_INFO_PATTERNS: List[str] = [
    r"api[_\s]?key\s*[=:]\s*\S+",
    r"password\s*[=:]\s*\S+",
    r"secret\s*[=:]\s*\S+",
    r"token\s*[=:]\s*[A-Za-z0-9+/=]{20,}",
    r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",  # email addresses
]

# Fitness domain facts that must NOT be contradicted
_FACTUAL_CONSTRAINTS: List[tuple[str, str]] = [
    (r"\bwarm[\s-]?up.{0,20}(unnecessary|skip|avoid|not\s+needed)\b",
     "Warm-up is always recommended before exercise"),
    (r"\bexercise.{0,30}(dangerous|harmful)\s+for\s+(everyone|all\s+people)\b",
     "Exercise is not dangerous for all people"),
    (r"\bdrink.{0,20}(no\s+water|water\s+is\s+bad)\b",
     "Hydration is essential during exercise"),
    (r"\bsleep.{0,20}(unnecessary|overrated|waste\s+of\s+time)\b",
     "Sleep is critical for recovery"),
]

MAX_RESPONSE_LENGTH = 4000


@dataclass
class OutputGuardrailResult:
    passed: bool
    violations: List[str] = field(default_factory=list)
    filtered_text: Optional[str] = None
    risk_score: float = 0.0


class OutputGuardrail:
    """Validates and filters AI-generated output before delivery."""

    def __init__(self) -> None:
        self._dangerous_re   = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in _DANGEROUS_CLAIM_PATTERNS]
        self._toxicity_re    = [re.compile(p, re.IGNORECASE) for p in _TOXICITY_PATTERNS]
        self._sensitive_re   = [re.compile(p, re.IGNORECASE) for p in _SENSITIVE_INFO_PATTERNS]
        self._factual_re     = [(re.compile(p, re.IGNORECASE | re.DOTALL), msg) for p, msg in _FACTUAL_CONSTRAINTS]

    def validate(self, text: str, expected_format: Optional[str] = None) -> OutputGuardrailResult:
        violations: List[str] = []
        risk = 0.0
        filtered = text

        # 1. Hallucination / dangerous medical claim detection
        for pattern in self._dangerous_re:
            if pattern.search(filtered):
                violations.append("Dangerous or potentially hallucinated medical claim detected")
                risk += 0.7
                break

        # 2. Factual accuracy validation
        for pattern, constraint_msg in self._factual_re:
            if pattern.search(filtered):
                violations.append(f"Factual constraint violated: {constraint_msg}")
                risk += 0.4

        # 3. Toxicity / harmful content filtering
        for pattern in self._toxicity_re:
            match = pattern.search(filtered)
            if match:
                violations.append("Toxic or harmful language detected in response")
                # Redact the offending sentence
                filtered = pattern.sub("[CONTENT REMOVED]", filtered)
                risk += 0.5

        # 4. Sensitive information filtering
        for pattern in self._sensitive_re:
            if pattern.search(filtered):
                violations.append("Sensitive information found in response; redacting")
                filtered = pattern.sub("[REDACTED]", filtered)
                risk += 0.6

        # 5. Response format validation
        if expected_format == "json":
            format_ok, format_err = self._validate_json(filtered)
            if not format_ok:
                violations.append(f"Response format validation failed: {format_err}")
                risk += 0.2

        # 6. Length check
        if len(filtered) > MAX_RESPONSE_LENGTH:
            filtered = filtered[:MAX_RESPONSE_LENGTH] + "\n\n[Response truncated for safety]"
            violations.append("Response exceeded maximum allowed length; truncated")
            risk += 0.1

        risk = min(risk, 1.0)
        hard_blocked = any(
            kw in v for v in violations
            for kw in ["Dangerous or potentially hallucinated", "Toxic or harmful"]
        )
        passed = not hard_blocked

        if violations:
            logger.warning("Output guardrail violations: %s", violations)

        return OutputGuardrailResult(
            passed=passed,
            violations=violations,
            filtered_text=filtered if passed else self._safe_fallback(),
            risk_score=risk,
        )

    # ------------------------------------------------------------------
    def _validate_json(self, text: str) -> tuple[bool, str]:
        try:
            json.loads(text)
            return True, ""
        except json.JSONDecodeError as exc:
            return False, str(exc)

    def _safe_fallback(self) -> str:
        return (
            "I'm sorry, I wasn't able to generate a safe response to that request. "
            "Please try rephrasing your question or consult a qualified fitness professional."
        )
