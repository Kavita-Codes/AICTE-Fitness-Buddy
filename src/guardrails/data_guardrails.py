"""
src/guardrails/data_guardrails.py
===================================
Guardrail 4 – Data Guardrails
Protects data accessed and processed by agents.

Checks performed:
  • Data privacy protection
  • Data masking and anonymisation
  • Role-based data access control
  • Database access restrictions
  • Prevention of unauthorised data retrieval
"""

from __future__ import annotations

import re
import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger("fitness_buddy")


class UserRole(str, Enum):
    GUEST = "guest"
    USER = "user"
    PREMIUM = "premium"
    ADMIN = "admin"


# ---------------------------------------------------------------------------
# Role-based access control table
# Data field → minimum role required to access
# ---------------------------------------------------------------------------
_FIELD_ACCESS_POLICY: Dict[str, UserRole] = {
    "user_id":          UserRole.GUEST,
    "fitness_goals":    UserRole.USER,
    "workout_history":  UserRole.USER,
    "meal_logs":        UserRole.USER,
    "bmi":              UserRole.USER,
    "progress_reports": UserRole.PREMIUM,
    "health_metrics":   UserRole.PREMIUM,
    "personal_records": UserRole.PREMIUM,
    "payment_info":     UserRole.ADMIN,
    "private_notes":    UserRole.ADMIN,
    "full_name":        UserRole.ADMIN,
    "date_of_birth":    UserRole.ADMIN,
    "medical_history":  UserRole.ADMIN,
    "location":         UserRole.ADMIN,
}

_ROLE_HIERARCHY: Dict[UserRole, int] = {
    UserRole.GUEST:   0,
    UserRole.USER:    1,
    UserRole.PREMIUM: 2,
    UserRole.ADMIN:   3,
}

# PII patterns for masking
_MASKING_PATTERNS: Dict[str, tuple[str, str]] = {
    "email":       (r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "[EMAIL]"),
    "phone":       (r"\b(\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b", "[PHONE]"),
    "ssn":         (r"\b\d{3}-\d{2}-\d{4}\b", "[SSN]"),
    "credit_card": (r"\b(?:\d[ -]?){13,16}\b", "[CARD]"),
    "dob":         (r"\b(0[1-9]|1[0-2])[/-](0[1-9]|[12]\d|3[01])[/-](\d{2}|\d{4})\b", "[DOB]"),
}

# Forbidden SQL operations that should never reach the DB layer
_FORBIDDEN_DB_OPERATIONS: List[str] = [
    r"\bDROP\s+(TABLE|DATABASE|INDEX|VIEW)\b",
    r"\bTRUNCATE\s+TABLE\b",
    r"\bDELETE\s+FROM\b(?!\s+\w+\s+WHERE)",  # DELETE without WHERE
    r"\bGRANT\b",
    r"\bREVOKE\b",
    r"\bCREATE\s+(USER|ROLE)\b",
    r"\bALTER\s+(USER|ROLE|TABLE)\b",
    r"xp_cmdshell",
    r"EXEC\s*\(",
    r"INTO\s+OUTFILE",
    r"LOAD_FILE\s*\(",
]


@dataclass
class DataGuardrailResult:
    passed: bool
    violations: List[str] = field(default_factory=list)
    masked_data: Optional[Any] = None
    filtered_fields: List[str] = field(default_factory=list)
    risk_score: float = 0.0


class DataGuardrail:
    """Enforces data privacy, masking, and role-based access control."""

    def __init__(self) -> None:
        self._mask_re = {
            name: (re.compile(pattern), replacement)
            for name, (pattern, replacement) in _MASKING_PATTERNS.items()
        }
        self._db_re = [re.compile(p, re.IGNORECASE) for p in _FORBIDDEN_DB_OPERATIONS]

    # ------------------------------------------------------------------
    # Masking
    # ------------------------------------------------------------------

    def mask_text(self, text: str) -> tuple[str, List[str]]:
        """Mask PII in a plain-text string. Returns (masked_text, list_of_types_masked)."""
        masked_types: List[str] = []
        for pii_type, (pattern, replacement) in self._mask_re.items():
            if pattern.search(text):
                text = pattern.sub(replacement, text)
                masked_types.append(pii_type)
        return text, masked_types

    def mask_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively mask PII in a dict payload."""
        result: Dict[str, Any] = {}
        for key, value in data.items():
            if isinstance(value, str):
                masked_val, _ = self.mask_text(value)
                result[key] = masked_val
            elif isinstance(value, dict):
                result[key] = self.mask_dict(value)
            else:
                result[key] = value
        return result

    # ------------------------------------------------------------------
    # Role-based access control
    # ------------------------------------------------------------------

    def check_field_access(
        self,
        requested_fields: List[str],
        user_role: UserRole,
    ) -> DataGuardrailResult:
        """Verify the caller's role permits access to each requested field."""
        violations: List[str] = []
        filtered: List[str] = []
        risk = 0.0
        caller_level = _ROLE_HIERARCHY.get(user_role, 0)

        for field_name in requested_fields:
            required_role = _FIELD_ACCESS_POLICY.get(field_name)
            if required_role is None:
                # Unknown field – deny by default
                filtered.append(field_name)
                violations.append(f"Field '{field_name}' is not in the access policy; access denied")
                risk += 0.3
            else:
                required_level = _ROLE_HIERARCHY[required_role]
                if caller_level < required_level:
                    filtered.append(field_name)
                    violations.append(
                        f"Insufficient role to access '{field_name}' "
                        f"(requires {required_role.value}, caller has {user_role.value})"
                    )
                    risk += 0.4

        risk = min(risk, 1.0)
        passed = len(violations) == 0

        if violations:
            logger.warning("Data guardrail RBAC violations: %s", violations)

        return DataGuardrailResult(
            passed=passed,
            violations=violations,
            filtered_fields=filtered,
            risk_score=risk,
        )

    # ------------------------------------------------------------------
    # Database query validation
    # ------------------------------------------------------------------

    def validate_db_query(self, query: str) -> DataGuardrailResult:
        """Prevent destructive or privilege-escalating DB operations."""
        violations: List[str] = []
        risk = 0.0

        for pattern in self._db_re:
            if pattern.search(query):
                violations.append(f"Forbidden database operation detected: {pattern.pattern[:60]}")
                risk += 0.9

        risk = min(risk, 1.0)
        passed = len(violations) == 0

        if violations:
            logger.error("Data guardrail DB violations: %s", violations)

        return DataGuardrailResult(passed=passed, violations=violations, risk_score=risk)

    # ------------------------------------------------------------------
    # Convenience: full validation pipeline
    # ------------------------------------------------------------------

    def validate(
        self,
        data: Any,
        user_role: UserRole = UserRole.USER,
        requested_fields: Optional[List[str]] = None,
        db_query: Optional[str] = None,
    ) -> DataGuardrailResult:
        violations: List[str] = []
        risk = 0.0
        masked_data = data

        # Mask PII in data
        if isinstance(data, dict):
            masked_data = self.mask_dict(data)
        elif isinstance(data, str):
            masked_data, masked_types = self.mask_text(data)
            if masked_types:
                violations.append(f"PII masked in data: {masked_types}")
                risk += 0.2

        # RBAC check
        if requested_fields:
            rbac_result = self.check_field_access(requested_fields, user_role)
            violations.extend(rbac_result.violations)
            risk += rbac_result.risk_score

        # DB query check
        if db_query:
            db_result = self.validate_db_query(db_query)
            violations.extend(db_result.violations)
            risk += db_result.risk_score

        risk = min(risk, 1.0)
        hard_blocked = any("Forbidden database" in v for v in violations)
        passed = not hard_blocked

        return DataGuardrailResult(
            passed=passed,
            violations=violations,
            masked_data=masked_data,
            risk_score=risk,
        )
