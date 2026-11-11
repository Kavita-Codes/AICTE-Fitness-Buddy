"""
src/guardrails/input_guardrails.py
===================================
Guardrail 1 – Input Guardrails
Validates every user message BEFORE it reaches the AI agent.

Checks performed:
  • Prompt injection detection
  • Malicious input detection
  • Input length / format validation
  • PII (Personally Identifiable Information) detection
  • Inappropriate content filtering
"""

from __future__ import annotations

import re
import json
import logging
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger("fitness_buddy")

# ---------------------------------------------------------------------------
# Known prompt-injection trigger phrases (case-insensitive)
# ---------------------------------------------------------------------------
_INJECTION_PATTERNS: List[str] = [
    r"ignore\s+(?:\w+\s+){0,3}(instructions?|prompts?|context|rules?|guidelines?)",
    r"ignore\s+(all|previous|prior|above)",
    r"forget\s+(everything|all|previous|prior)",
    r"you\s+are\s+now\s+(a\s+)?(?!fitness|wellness|health)",
    r"act\s+as\s+(if\s+you\s+are\s+)?(?!a\s+fitness)",
    r"pretend\s+(you\s+are|to\s+be)\s+(?!a\s+fitness)",
    r"disregard\s+(your|all|the)\s+(previous|instructions?|rules?|guidelines?)",
    r"new\s+instructions?:",
    r"system\s*:\s*you\s+are",
    r"<\s*system\s*>",
    r"\[system\]",
    r"jailbreak",
    r"dan\s+mode",
    r"developer\s+mode\s+enabled",
]

_JAILBREAK_PATTERNS: List[str] = [
    r"do\s+anything\s+now",
    r"without\s+(any\s+)?restrictions?",
    r"no\s+(content|safety)\s+filter",
    r"bypass\s+(safety|filter|guardrail|restriction)",
    r"uncensored\s+mode",
    r"override\s+(safety|filter|restriction)",
]

_MALICIOUS_PATTERNS: List[str] = [
    r"<\s*script",
    r"javascript\s*:",
    r"on\w+\s*=",           # HTML event handlers
    r"\beval\s*\(",
    r"\bexec\s*\(",
    r"__import__\s*\(",
    r"subprocess",
    r"os\.system",
    r"base64\.b64decode",
]

_INAPPROPRIATE_KEYWORDS: List[str] = [
    r"\bporn\b",
    r"\bsex\b(?!\s*ual\s+health)",  # allow "sexual health"
    r"\bviol[ae]nc[ey]\b",
    r"\bhate\s+speech\b",
    r"\bracis[mt]\b",
    r"\bslur\b",
    r"\bself[\s-]?harm\b",
    r"\bsuicid[ea]\b",
]

# PII patterns
_PII_PATTERNS: dict[str, str] = {
    "email":        r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
    "phone_us":     r"\b(\+1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b",
    "ssn":          r"\b\d{3}-\d{2}-\d{4}\b",
    "credit_card":  r"\b(?:\d[ -]?){13,16}\b",
    "ip_address":   r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
}

MAX_INPUT_LENGTH = 2000   # characters


@dataclass
class InputGuardrailResult:
    passed: bool
    violations: List[str] = field(default_factory=list)
    sanitized_text: Optional[str] = None
    risk_score: float = 0.0   # 0.0 (safe) – 1.0 (blocked)


class InputGuardrail:
    """Validates and sanitises raw user input."""

    def __init__(self) -> None:
        self._injection_re  = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in _INJECTION_PATTERNS]
        self._jailbreak_re  = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in _JAILBREAK_PATTERNS]
        self._malicious_re  = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in _MALICIOUS_PATTERNS]
        self._inappropriate_re = [re.compile(p, re.IGNORECASE) for p in _INAPPROPRIATE_KEYWORDS]
        self._pii_re        = {k: re.compile(v) for k, v in _PII_PATTERNS.items()}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate(self, text: str) -> InputGuardrailResult:
        """Run all input checks and return a result object."""
        violations: List[str] = []
        risk = 0.0
        sanitized = text

        # 1. Length / format validation
        if not text or not text.strip():
            return InputGuardrailResult(passed=False, violations=["Empty input"], risk_score=0.1)

        if len(text) > MAX_INPUT_LENGTH:
            violations.append(f"Input exceeds maximum length ({len(text)} > {MAX_INPUT_LENGTH})")
            sanitized = text[:MAX_INPUT_LENGTH]
            risk += 0.1

        # 2. Malicious input detection (HTML/script injection)
        for pattern in self._malicious_re:
            if pattern.search(text):
                violations.append("Malicious content detected (script/code injection)")
                risk += 0.5
                break

        # 3. Prompt injection detection
        for pattern in self._injection_re:
            if pattern.search(text):
                violations.append("Prompt injection attempt detected")
                risk += 0.6
                break

        # 4. Jailbreak detection
        for pattern in self._jailbreak_re:
            if pattern.search(text):
                violations.append("Jailbreak attempt detected")
                risk += 0.7
                break

        # 5. Inappropriate content filtering
        for pattern in self._inappropriate_re:
            if pattern.search(text):
                violations.append("Inappropriate content detected")
                risk += 0.4
                break

        # 6. PII detection (warn but do NOT block – redact instead)
        pii_found: List[str] = []
        for pii_type, pattern in self._pii_re.items():
            matches = pattern.findall(sanitized)
            if matches:
                pii_found.append(pii_type)
                sanitized = pattern.sub(f"[{pii_type.upper()}_REDACTED]", sanitized)

        if pii_found:
            violations.append(f"PII detected and redacted: {', '.join(pii_found)}")
            risk += 0.2
            logger.warning("PII detected in user input: %s", pii_found)

        risk = min(risk, 1.0)

        # Block if critical violation or high risk
        hard_block_keywords = [
            "Malicious content",
            "Prompt injection",
            "Jailbreak",
            "Inappropriate content",
        ]
        hard_blocked = any(
            any(kw in v for kw in hard_block_keywords) for v in violations
        )
        passed = not hard_blocked

        if violations:
            logger.warning("Input guardrail violations: %s", violations)

        return InputGuardrailResult(
            passed=passed,
            violations=violations,
            sanitized_text=sanitized if passed else None,
            risk_score=risk,
        )
