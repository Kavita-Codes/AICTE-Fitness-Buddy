"""
src/guardrails/tool_guardrails.py
===================================
Guardrail 3 – Tool Execution Guardrails
Controls how AI agents interact with external tools and APIs.

Checks performed:
  • Tool access permissions (allowlist)
  • API authorisation validation
  • Function-call parameter validation
  • Restricted tool execution enforcement
  • Prevention of unauthorised actions
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger("fitness_buddy")

# ---------------------------------------------------------------------------
# Allowlisted tools the AI agent is permitted to call
# ---------------------------------------------------------------------------
ALLOWED_TOOLS: Set[str] = {
    "get_workout_plan",
    "get_nutrition_tips",
    "get_motivation_message",
    "get_wellness_guidance",
    "search_fitness_knowledge",
    "calculate_bmi",
    "calculate_calories",
    "get_exercise_details",
    "get_meal_suggestion",
}

# Tools that require human-in-the-loop approval before execution
HUMAN_APPROVAL_REQUIRED: Set[str] = {
    "send_email",
    "modify_user_profile",
    "delete_user_data",
    "export_user_data",
    "financial_transaction",
}

# Tools that are explicitly forbidden
FORBIDDEN_TOOLS: Set[str] = {
    "execute_code",
    "run_shell_command",
    "access_filesystem",
    "database_admin",
    "send_sms",
    "access_credentials",
    "modify_system_settings",
}

# Parameter schemas for critical tool calls
_TOOL_PARAM_SCHEMAS: Dict[str, Dict[str, type]] = {
    "calculate_bmi": {"weight_kg": float, "height_m": float},
    "calculate_calories": {"weight_kg": float, "height_m": float, "age": int, "activity_level": str},
    "get_workout_plan": {"fitness_goal": str, "experience_level": str},
    "get_meal_suggestion": {"dietary_preference": str},
}

# SQL injection patterns (for any tool receiving raw query strings)
_SQL_INJECTION_PATTERNS: List[str] = [
    r"(\s|;|'|\")(DROP|DELETE|INSERT|UPDATE|ALTER|TRUNCATE|CREATE|REPLACE)\s+",
    r"UNION\s+SELECT",
    r"OR\s+1\s*=\s*1",
    r"--\s*$",
    r";\s*(DROP|DELETE|INSERT)",
    r"xp_cmdshell",
    r"EXEC\s*\(",
]


@dataclass
class ToolGuardrailResult:
    passed: bool
    tool_name: str
    violations: List[str] = field(default_factory=list)
    requires_approval: bool = False
    risk_score: float = 0.0


class ToolGuardrail:
    """Validates AI agent tool calls before execution."""

    def __init__(self) -> None:
        self._sql_re = [re.compile(p, re.IGNORECASE) for p in _SQL_INJECTION_PATTERNS]

    def validate(
        self,
        tool_name: str,
        parameters: Optional[Dict[str, Any]] = None,
        caller_id: Optional[str] = None,
    ) -> ToolGuardrailResult:
        violations: List[str] = []
        risk = 0.0
        parameters = parameters or {}

        # 1. Check forbidden tools
        if tool_name in FORBIDDEN_TOOLS:
            violations.append(f"Tool '{tool_name}' is explicitly forbidden")
            risk = 1.0
            logger.error("Forbidden tool call attempted: %s by %s", tool_name, caller_id)
            return ToolGuardrailResult(
                passed=False, tool_name=tool_name, violations=violations, risk_score=risk
            )

        # 2. Check against allowlist
        requires_approval = tool_name in HUMAN_APPROVAL_REQUIRED
        if tool_name not in ALLOWED_TOOLS and not requires_approval:
            violations.append(f"Tool '{tool_name}' is not in the allowed tools list")
            risk += 0.8
            logger.warning("Unknown tool call attempted: %s", tool_name)

        # 3. Human approval requirement
        if requires_approval:
            violations.append(f"Tool '{tool_name}' requires human approval before execution")
            risk += 0.3
            logger.info("Human approval required for tool: %s", tool_name)

        # 4. Parameter validation
        schema = _TOOL_PARAM_SCHEMAS.get(tool_name)
        if schema:
            param_errors = self._validate_params(parameters, schema)
            violations.extend(param_errors)
            if param_errors:
                risk += 0.3

        # 5. SQL injection prevention – scan all string params
        for param_name, param_value in parameters.items():
            if isinstance(param_value, str):
                for pattern in self._sql_re:
                    if pattern.search(param_value):
                        violations.append(
                            f"SQL injection detected in parameter '{param_name}'"
                        )
                        risk += 0.9
                        logger.error("SQL injection attempt in tool params: %s=%s", param_name, param_value)
                        break

        risk = min(risk, 1.0)
        hard_blocked = any(
            kw in v for v in violations
            for kw in ["explicitly forbidden", "SQL injection"]
        )
        passed = not hard_blocked

        if violations:
            logger.warning("Tool guardrail '%s': %s", tool_name, violations)

        return ToolGuardrailResult(
            passed=passed,
            tool_name=tool_name,
            violations=violations,
            requires_approval=requires_approval,
            risk_score=risk,
        )

    # ------------------------------------------------------------------
    def _validate_params(
        self, params: Dict[str, Any], schema: Dict[str, type]
    ) -> List[str]:
        errors: List[str] = []
        for param, expected_type in schema.items():
            if param not in params:
                errors.append(f"Required parameter '{param}' is missing")
            elif not isinstance(params[param], expected_type):
                errors.append(
                    f"Parameter '{param}' expected {expected_type.__name__}, "
                    f"got {type(params[param]).__name__}"
                )
        return errors
