"""
src/agents/orchestrator.py
============================
Multi-agent Orchestrator for Fitness Buddy.

Routes user requests to the appropriate specialised sub-agent:
  • workout_agent   – exercise plans and routines
  • nutrition_agent – meal suggestions and calorie info
  • motivation_agent– daily inspiration and habit building
  • wellness_agent  – sleep, hydration, stress management
  • safety_agent    – validates all outputs before delivery

All routing goes through the Multi-Agent Guardrail to enforce
access control, task validation, and loop detection.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, Optional

from src.guardrails.multi_agent_guardrails import (
    AgentMessage,
    AgentRole,
    MultiAgentGuardrail,
)
from src.utils.logger import setup_logger, setup_audit_logger

logger = setup_logger("fitness_buddy.orchestrator")
setup_audit_logger()


# ---------------------------------------------------------------------------
# Intent → Agent routing table
# ---------------------------------------------------------------------------
_INTENT_KEYWORDS: Dict[AgentRole, list[str]] = {
    AgentRole.WORKOUT_AGENT:    ["workout", "exercise", "training", "routine", "gym", "push-up", "squat", "run", "cardio", "weight", "muscle", "strength", "hiit", "yoga", "stretch", "flexibility"],
    AgentRole.NUTRITION_AGENT:  ["meal", "food", "eat", "diet", "nutrition", "calorie", "protein", "carb", "fat", "recipe", "snack", "breakfast", "lunch", "dinner", "vegetarian", "vegan", "bmi", "tdee", "bmr"],
    AgentRole.MOTIVATION_AGENT: ["motivat", "inspire", "encourage", "tip", "quote", "goal", "habit", "consistency", "mindset", "positive", "challenge"],
    AgentRole.WELLNESS_AGENT:   ["sleep", "rest", "recover", "hydrat", "water", "drink", "stress", "mental", "relax", "anxiety", "wellness", "breathe", "mindful", "meditat"],
}


def _detect_intent(message: str) -> AgentRole:
    """Map user message to the most appropriate sub-agent."""
    msg_lower = message.lower()
    scores: Dict[AgentRole, int] = {role: 0 for role in _INTENT_KEYWORDS}
    for role, keywords in _INTENT_KEYWORDS.items():
        for kw in keywords:
            if kw in msg_lower:
                scores[role] += 1
    best = max(scores, key=lambda r: scores[r])
    return best if scores[best] > 0 else AgentRole.WORKOUT_AGENT


class FitnessOrchestrator:
    """
    Routes incoming requests to specialist agents and assembles
    the final response with full multi-agent guardrail checks.
    """

    def __init__(self) -> None:
        from src.agents.fitness_agent import FitnessAgent
        from src.guardrails.data_guardrails import UserRole

        # One shared FitnessAgent (holds Granite client + all guardrails)
        self._agent = FitnessAgent(user_role=UserRole.USER)
        self._ma_guard = MultiAgentGuardrail()
        logger.info("FitnessOrchestrator ready")

    # ------------------------------------------------------------------
    # Public: process query
    # ------------------------------------------------------------------

    def process_query(
        self,
        user_message: str,
        session_id: Optional[str] = None,
        user_id: str = "anonymous",
    ) -> Dict[str, Any]:
        """
        Full orchestration pipeline:
          1. Detect intent → select sub-agent
          2. Validate communication via Multi-Agent Guardrail
          3. Delegate to sub-agent (FitnessAgent)
          4. Validate output via Multi-Agent Guardrail
          5. Return enriched response
        """
        session_id = session_id or str(uuid.uuid4())
        target_agent = _detect_intent(user_message)

        # ── Step 1: Validate orchestrator → sub-agent message ─────────
        msg = AgentMessage(
            sender=AgentRole.ORCHESTRATOR,
            receiver=target_agent,
            task=self._agent_task(target_agent),
            session_id=session_id,
        )
        ma_result = self._ma_guard.validate_message(msg)
        if not ma_result.passed:
            logger.error("Multi-agent guardrail blocked routing: %s", ma_result.violations)
            return {
                "response": "⚠️ Unable to process your request due to routing policy restrictions.",
                "session_id": session_id,
                "status": "blocked",
                "agent": target_agent.value,
                "guardrails_triggered": ["multi_agent_guardrail"],
                "powered_by": "IBM watsonx.ai (Granite)",
            }

        logger.info(
            "Routing request [session=%s] → %s (task=%s)",
            session_id, target_agent.value, msg.task,
        )

        # ── Step 2: Delegate to specialist agent ──────────────────────
        result = self._agent.chat(
            user_message=user_message,
            session_id=session_id,
            user_id=user_id,
        )

        # ── Step 3: Cross-agent output verification ───────────────────
        output_check = self._ma_guard.verify_cross_agent_output(
            sender=target_agent,
            output=result.get("response", ""),
        )
        if not output_check.passed:
            result["guardrails_triggered"] = result.get("guardrails_triggered", []) + ["multi_agent_output_guardrail"]
            result["warnings"] = result.get("warnings", []) + output_check.violations
            logger.warning("Multi-agent output check: %s", output_check.violations)

        result["agent"] = target_agent.value
        result["orchestrator"] = "fitness_orchestrator"
        return result

    # ------------------------------------------------------------------
    def _agent_task(self, role: AgentRole) -> str:
        mapping = {
            AgentRole.WORKOUT_AGENT:    "suggest_workout",
            AgentRole.NUTRITION_AGENT:  "suggest_meal",
            AgentRole.MOTIVATION_AGENT: "motivational_quote",
            AgentRole.WELLNESS_AGENT:   "sleep_advice",
        }
        return mapping.get(role, "route_request")

    def reset_session(self) -> None:
        self._agent.reset_conversation()

    @property
    def is_granite_active(self) -> bool:
        return self._agent.is_granite_active
