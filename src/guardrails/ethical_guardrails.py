"""
src/guardrails/ethical_guardrails.py
======================================
Guardrail 9 – Ethical and Compliance Guardrails
Ensures responsible and compliant AI behaviour.

Checks performed:
  • Bias detection
  • Fairness validation
  • Explainability (response transparency)
  • Regulatory compliance (GDPR / HIPAA awareness)
  • Responsible AI principles
  • Audit trail generation
"""

from __future__ import annotations

import json
import logging
import re
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("fitness_buddy")
audit_logger = logging.getLogger("audit")

# ---------------------------------------------------------------------------
# Bias indicators – language that may reflect demographic bias
# ---------------------------------------------------------------------------
_BIAS_PATTERNS: List[tuple[str, str]] = [
    (r"\b(men|women)\s+(can'?t|cannot|are\s+unable\s+to)\s+\w+\b",
     "Gender-based capability claim"),
    (r"\b(old(er)?|elderly|senior)\s+people\s+(can'?t|cannot|shouldn'?t)\b",
     "Age-based capability restriction"),
    (r"\b(obese|fat)\s+people\s+\w+\b",
     "Body-shaming or weight-based bias"),
    (r"\b(beginners?|novice)\s+are\s+(too\s+)?(weak|unfit|not\s+ready)\b",
     "Fitness-level disparagement"),
    (r"\b(only|just)\s+(thin|slim|fit)\s+people\b",
     "Exclusionary fitness framing"),
    (r"\byou\s+(look|seem|appear)\s+(fat|overweight|unhealthy)\b",
     "Appearance-shaming"),
]

# Regulatory compliance terms that require a disclaimer
_MEDICAL_DISCLAIMER_TRIGGERS: List[str] = [
    r"\b(diagnos|prescri|treat|cure|medic)\w*\b",
    r"\bclinical\s+(trial|study|evidence)\b",
    r"\b(disease|disorder|condition|syndrome)\b",
    r"\b(doctor|physician|therapist|dietitian)\s+recommended\b",
]

MEDICAL_DISCLAIMER = (
    "\n\n⚠️ **Disclaimer:** This information is for general wellness and fitness purposes "
    "only and does not constitute medical advice. Please consult a qualified healthcare "
    "professional before making any health-related decisions."
)

GDPR_DATA_CATEGORIES = {
    "health_data", "biometric_data", "genetic_data",
    "medical_history", "mental_health", "location_data",
}


@dataclass
class AuditEntry:
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    session_id: str = ""
    user_id: str = ""
    event_type: str = ""
    input_summary: str = ""
    output_summary: str = ""
    guardrails_triggered: List[str] = field(default_factory=list)
    risk_score: float = 0.0
    decision: str = "allowed"

    def to_json(self) -> str:
        return json.dumps(asdict(self))


@dataclass
class EthicalGuardrailResult:
    passed: bool
    violations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    enriched_text: Optional[str] = None
    risk_score: float = 0.0
    audit_entry: Optional[AuditEntry] = None


class EthicalGuardrail:
    """
    Enforces responsible AI principles: bias, fairness, explainability,
    GDPR/HIPAA compliance awareness, and immutable audit trails.
    """

    def __init__(self) -> None:
        from src.config import get_settings
        s = get_settings()
        self._audit_enabled = s.enable_audit_trail
        self._audit_path = Path(s.audit_log_path)
        self._audit_path.parent.mkdir(parents=True, exist_ok=True)

        self._bias_re = [(re.compile(p, re.IGNORECASE), msg) for p, msg in _BIAS_PATTERNS]
        self._medical_re = [re.compile(p, re.IGNORECASE) for p in _MEDICAL_DISCLAIMER_TRIGGERS]

    # ------------------------------------------------------------------
    # Main validation
    # ------------------------------------------------------------------

    def validate(
        self,
        text: str,
        session_id: str = "",
        user_id: str = "",
        input_text: str = "",
        guardrails_triggered: Optional[List[str]] = None,
    ) -> EthicalGuardrailResult:
        violations: List[str] = []
        warnings: List[str] = []
        risk = 0.0
        enriched = text

        # 1. Bias detection
        for pattern, description in self._bias_re:
            if pattern.search(text):
                violations.append(f"Potential bias detected: {description}")
                risk += 0.4

        # 2. Fairness – inclusive language check
        exclusionary_re = re.compile(
            r"\b(only|exclusively|solely)\s+(for\s+)?(men|women|young|thin|fit)\b",
            re.IGNORECASE,
        )
        if exclusionary_re.search(text):
            warnings.append("Non-inclusive language detected; consider rephrasing for broader audience")
            risk += 0.2

        # 3. Regulatory compliance – add medical disclaimer when needed
        needs_disclaimer = any(p.search(text) for p in self._medical_re)
        if needs_disclaimer and MEDICAL_DISCLAIMER not in text:
            enriched = text + MEDICAL_DISCLAIMER
            warnings.append("Medical disclaimer appended for regulatory compliance")

        # 4. Explainability – check that advice includes a rationale
        if len(text) > 200:
            has_rationale = bool(re.search(
                r"\b(because|since|as\s+a\s+result|this\s+is\s+because|reason|why|therefore|helps?)\b",
                text, re.IGNORECASE,
            ))
            if not has_rationale:
                warnings.append("Response lacks explanatory rationale; consider adding 'because/why' context")

        # 5. GDPR data category check – warn if sensitive health data in output
        for category in GDPR_DATA_CATEGORIES:
            if re.search(rf"\b{re.escape(category.replace('_', ' '))}\b", text, re.IGNORECASE):
                warnings.append(
                    f"GDPR-sensitive category '{category}' referenced; ensure data minimisation"
                )
                risk += 0.15

        risk = min(risk, 1.0)
        hard_blocked = risk >= 0.8

        # 6. Audit trail
        audit_entry = self._write_audit(
            session_id=session_id,
            user_id=user_id,
            input_text=input_text,
            output_text=enriched,
            guardrails_triggered=guardrails_triggered or [],
            violations=violations,
            warnings=warnings,
            risk_score=risk,
            decision="blocked" if hard_blocked else "allowed",
        )

        if violations:
            logger.warning("Ethical guardrail violations: %s", violations)
        if warnings:
            logger.info("Ethical guardrail warnings: %s", warnings)

        return EthicalGuardrailResult(
            passed=not hard_blocked,
            violations=violations,
            warnings=warnings,
            enriched_text=enriched,
            risk_score=risk,
            audit_entry=audit_entry,
        )

    # ------------------------------------------------------------------
    # Audit trail
    # ------------------------------------------------------------------

    def _write_audit(
        self,
        session_id: str,
        user_id: str,
        input_text: str,
        output_text: str,
        guardrails_triggered: List[str],
        violations: List[str],
        warnings: List[str],
        risk_score: float,
        decision: str,
    ) -> AuditEntry:
        entry = AuditEntry(
            session_id=session_id,
            user_id=user_id,
            event_type="guardrail_evaluation",
            input_summary=input_text[:200],
            output_summary=output_text[:200],
            guardrails_triggered=guardrails_triggered + violations + warnings,
            risk_score=risk_score,
            decision=decision,
        )
        if self._audit_enabled:
            audit_logger.info(entry.to_json())
        return entry

    def write_custom_audit(self, event_type: str, details: Dict[str, Any]) -> None:
        """Write a custom audit entry for any significant event."""
        if not self._audit_enabled:
            return
        entry = {
            "event_id": str(uuid.uuid4()),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "event_type": event_type,
            **details,
        }
        audit_logger.info(json.dumps(entry))
