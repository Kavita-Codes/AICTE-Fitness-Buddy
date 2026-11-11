"""
src/guardrails/security_guardrails.py
========================================
Guardrail 5 – Security Guardrails
Protects the application from security threats.

Checks performed:
  • Prompt injection protection
  • Jailbreak detection (advanced)
  • SQL injection prevention
  • Cross-agent communication security (token validation)
  • Credential and secret management enforcement
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("fitness_buddy")

# ---------------------------------------------------------------------------
# Advanced prompt injection & jailbreak patterns
# ---------------------------------------------------------------------------
_ADVANCED_INJECTION_PATTERNS: List[str] = [
    # Classic instruction override
    r"ignore\s+(all\s+)?(previous|prior|above|your)\s+(instructions?|prompts?|rules?)",
    r"disregard\s+(your\s+)?(previous|prior|original)\s+(instructions?|programming|training)",
    r"forget\s+(everything|all|your\s+instructions?|your\s+training)",
    # Role hijacking
    r"you\s+(are|must|should|will)\s+(now\s+)?(act|behave|respond)\s+as\s+(?!a\s+fitness)",
    r"your\s+new\s+(role|persona|identity|instructions?)\s+(is|are)",
    r"(switch|change)\s+(to|into)\s+(evil|unrestricted|unfiltered|uncensored)\s+mode",
    # Hidden instruction injection
    r"<!--.*?-->",                       # HTML comments
    r"\{%.*?%\}",                        # template injection
    r"\{\{.*?\}\}",                      # template injection
    r"<\s*(instruction|system|prompt)\s*>",
    # Multi-turn manipulation
    r"in\s+a\s+hypothetical\s+(scenario|world|universe).{0,60}(how\s+to\s+(harm|kill|hurt|attack))",
    r"for\s+(educational|research|fictional)\s+purposes.{0,40}(tell\s+me\s+how\s+to)",
]

_JAILBREAK_ADVANCED: List[str] = [
    r"\bDAN\b",                          # Do Anything Now
    r"grandma\s+(used\s+to\s+)?(tell|read|explain)",  # grandma exploit
    r"(napalm|bomb|exploit|malware|ransomware)\s+(recipe|formula|code|tutorial)",
    r"pretend\s+(the\s+)?AI\s+(has\s+)?no\s+(restrictions?|filters?|guidelines?)",
    r"(enable|activate|turn\s+on)\s+(developer|god|chaos|evil|unlimited)\s+mode",
    r"do\s+anything\s+now",
    r"you\s+have\s+(been\s+)?(freed|liberated|unlocked)",
    r"(bypass|circumvent|override)\s+(your\s+)?(safety|guardrail|filter|restriction|limit)",
]

_SQL_INJECTION_FULL: List[str] = [
    r"(;|\b)(DROP|DELETE|TRUNCATE|ALTER)\s+(TABLE|DATABASE|VIEW|INDEX)\b",
    r"\bUNION\b.{0,50}\bSELECT\b",
    r"\bOR\b\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+['\"]?",
    r"\bAND\b\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+['\"]?",
    r"--\s*(#.*)?$",
    r"/\*.*?\*/",
    r"\b(EXEC|EXECUTE)\s*(\(|xp_)",
    r"(?:;|%3B)\s*(DROP|INSERT|UPDATE|DELETE)",
    r"\bINTO\s+OUTFILE\b",
    r"\bLOAD_FILE\s*\(",
    r"\bINFORMATION_SCHEMA\b",
    r"\bsys\.tables\b",
]

# Patterns that should NEVER appear in credentials/configs at runtime
_CREDENTIAL_LEAK_PATTERNS: List[str] = [
    r"(password|passwd|pwd)\s*[:=]\s*[^\s]{4,}",
    r"(api[_-]?key|apikey|api[_-]?secret)\s*[:=]\s*[^\s]{8,}",
    r"(secret[_-]?key|secret)\s*[:=]\s*[^\s]{8,}",
    r"(access[_-]?token|auth[_-]?token|bearer)\s*[:=]\s*[^\s]{8,}",
    r"(private[_-]?key)\s*[:=]",
    r"sk-[A-Za-z0-9]{20,}",          # OpenAI key pattern
    r"AIza[A-Za-z0-9_-]{35}",        # Google API key pattern
]


@dataclass
class SecurityGuardrailResult:
    passed: bool
    threat_type: Optional[str] = None
    violations: List[str] = field(default_factory=list)
    risk_score: float = 0.0


class SecurityGuardrail:
    """
    Comprehensive security guardrail for prompt injection, jailbreak,
    SQL injection, cross-agent auth, and credential leak prevention.
    """

    def __init__(self, secret_key: str = "") -> None:
        self._secret_key = secret_key.encode() if secret_key else b"fitness_buddy_default_key"
        self._injection_re   = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in _ADVANCED_INJECTION_PATTERNS]
        self._jailbreak_re   = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in _JAILBREAK_ADVANCED]
        self._sql_re         = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in _SQL_INJECTION_FULL]
        self._credential_re  = [re.compile(p, re.IGNORECASE) for p in _CREDENTIAL_LEAK_PATTERNS]

    # ------------------------------------------------------------------
    # Main validation entry point
    # ------------------------------------------------------------------

    def validate(self, text: str) -> SecurityGuardrailResult:
        """Run all security checks on the provided text."""
        violations: List[str] = []
        risk = 0.0
        threat_type: Optional[str] = None

        # 1. Prompt injection
        for pattern in self._injection_re:
            if pattern.search(text):
                violations.append("Prompt injection attempt detected")
                threat_type = "prompt_injection"
                risk += 0.8
                break

        # 2. Jailbreak
        for pattern in self._jailbreak_re:
            if pattern.search(text):
                violations.append("Jailbreak attempt detected")
                if not threat_type:
                    threat_type = "jailbreak"
                risk += 0.9
                break

        # 3. SQL injection
        for pattern in self._sql_re:
            if pattern.search(text):
                violations.append("SQL injection attempt detected")
                if not threat_type:
                    threat_type = "sql_injection"
                risk += 0.8
                break

        # 4. Credential leak prevention
        for pattern in self._credential_re:
            if pattern.search(text):
                violations.append("Potential credential/secret leak detected in input")
                if not threat_type:
                    threat_type = "credential_leak"
                risk += 0.6
                break

        risk = min(risk, 1.0)
        passed = len(violations) == 0

        if violations:
            logger.error("SECURITY ALERT – %s violations: %s", threat_type, violations)

        return SecurityGuardrailResult(
            passed=passed,
            threat_type=threat_type,
            violations=violations,
            risk_score=risk,
        )

    # ------------------------------------------------------------------
    # Cross-agent communication security
    # ------------------------------------------------------------------

    def generate_agent_token(self, agent_id: str, timestamp: Optional[int] = None) -> str:
        """Generate an HMAC-based token for cross-agent message authentication."""
        ts = timestamp or int(time.time())
        payload = f"{agent_id}:{ts}"
        signature = hmac.new(self._secret_key, payload.encode(), hashlib.sha256).hexdigest()
        return f"{payload}:{signature}"

    def verify_agent_token(self, token: str, max_age_seconds: int = 60) -> bool:
        """Verify an agent token is authentic and not expired."""
        try:
            parts = token.split(":")
            if len(parts) != 3:
                return False
            agent_id, ts_str, received_sig = parts
            ts = int(ts_str)

            # Check expiry
            if int(time.time()) - ts > max_age_seconds:
                logger.warning("Expired agent token from: %s", agent_id)
                return False

            # Verify signature
            payload = f"{agent_id}:{ts}"
            expected_sig = hmac.new(self._secret_key, payload.encode(), hashlib.sha256).hexdigest()
            return hmac.compare_digest(expected_sig, received_sig)
        except Exception as exc:
            logger.error("Agent token verification error: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Credential management check
    # ------------------------------------------------------------------

    def scan_for_credential_leaks(self, data: Dict[str, Any]) -> List[str]:
        """Scan a dictionary for any accidental credential exposure."""
        leaks: List[str] = []
        for key, value in data.items():
            if isinstance(value, str):
                for pattern in self._credential_re:
                    if pattern.search(value):
                        leaks.append(f"Potential credential leak in field '{key}'")
                        logger.error("Credential leak detected in field: %s", key)
                        break
        return leaks
