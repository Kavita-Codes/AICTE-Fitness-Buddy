"""
src/guardrails/multi_agent_guardrails.py
==========================================
Guardrail 8 – Multi-Agent Guardrails
Ensures safe coordination between multiple specialised agents.

Checks performed:
  • Agent-level access control
  • Task assignment validation
  • Cross-agent output verification
  • Agent communication monitoring
  • Conflict resolution between agents
  • Prevention of infinite agent loops
"""

from __future__ import annotations

import logging
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger("fitness_buddy")


class AgentRole(str, Enum):
    ORCHESTRATOR   = "orchestrator"
    WORKOUT_AGENT  = "workout_agent"
    NUTRITION_AGENT = "nutrition_agent"
    MOTIVATION_AGENT = "motivation_agent"
    WELLNESS_AGENT = "wellness_agent"
    SAFETY_AGENT   = "safety_agent"


# ---------------------------------------------------------------------------
# Agent communication allowlist:
#   sender → set of agents it is allowed to communicate with
# ---------------------------------------------------------------------------
_AGENT_COMM_POLICY: Dict[AgentRole, Set[AgentRole]] = {
    AgentRole.ORCHESTRATOR:    {AgentRole.WORKOUT_AGENT, AgentRole.NUTRITION_AGENT,
                                 AgentRole.MOTIVATION_AGENT, AgentRole.WELLNESS_AGENT,
                                 AgentRole.SAFETY_AGENT},
    AgentRole.WORKOUT_AGENT:   {AgentRole.ORCHESTRATOR, AgentRole.SAFETY_AGENT},
    AgentRole.NUTRITION_AGENT: {AgentRole.ORCHESTRATOR, AgentRole.SAFETY_AGENT},
    AgentRole.MOTIVATION_AGENT:{AgentRole.ORCHESTRATOR},
    AgentRole.WELLNESS_AGENT:  {AgentRole.ORCHESTRATOR, AgentRole.SAFETY_AGENT},
    AgentRole.SAFETY_AGENT:    {AgentRole.ORCHESTRATOR},
}

# Tasks each agent is authorised to handle
_AGENT_TASK_POLICY: Dict[AgentRole, Set[str]] = {
    AgentRole.ORCHESTRATOR:    {"route_request", "aggregate_response", "delegate_task"},
    AgentRole.WORKOUT_AGENT:   {"suggest_workout", "explain_exercise", "build_routine"},
    AgentRole.NUTRITION_AGENT: {"suggest_meal", "calculate_calories", "nutrition_info"},
    AgentRole.MOTIVATION_AGENT:{"motivational_quote", "daily_tip", "habit_suggestion"},
    AgentRole.WELLNESS_AGENT:  {"sleep_advice", "hydration_tip", "stress_management"},
    AgentRole.SAFETY_AGENT:    {"validate_output", "check_safety", "escalate"},
}

MAX_LOOP_CYCLES = 5     # Maximum times a task can be re-delegated before loop detection fires


@dataclass
class AgentMessage:
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender: AgentRole = AgentRole.ORCHESTRATOR
    receiver: AgentRole = AgentRole.ORCHESTRATOR
    task: str = ""
    payload: Optional[Dict[str, Any]] = None
    timestamp: float = field(default_factory=time.time)
    hops: int = 0               # number of times this message has been forwarded
    session_id: str = ""


@dataclass
class MultiAgentGuardrailResult:
    passed: bool
    violations: List[str] = field(default_factory=list)
    risk_score: float = 0.0


class MultiAgentGuardrail:
    """
    Manages safe multi-agent coordination:
    access control, task validation, loop detection, and output verification.
    """

    def __init__(self) -> None:
        # session_id → list of (sender, receiver, task, timestamp)
        self._message_log: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        # session_id → task → delegation count
        self._delegation_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    # ------------------------------------------------------------------
    # Communication check
    # ------------------------------------------------------------------

    def validate_message(self, message: AgentMessage) -> MultiAgentGuardrailResult:
        violations: List[str] = []
        risk = 0.0

        # 1. Agent communication access control
        allowed_receivers = _AGENT_COMM_POLICY.get(message.sender, set())
        if message.receiver not in allowed_receivers:
            violations.append(
                f"Agent '{message.sender}' is not permitted to communicate with '{message.receiver}'"
            )
            risk += 0.7

        # 2. Task assignment validation
        allowed_tasks = _AGENT_TASK_POLICY.get(message.receiver, set())
        if message.task not in allowed_tasks:
            violations.append(
                f"Agent '{message.receiver}' is not authorised to handle task '{message.task}'"
            )
            risk += 0.5

        # 3. Infinite loop detection
        self._delegation_counts[message.session_id][message.task] += 1
        count = self._delegation_counts[message.session_id][message.task]
        if count > MAX_LOOP_CYCLES:
            violations.append(
                f"Infinite agent loop detected: task '{message.task}' delegated {count} times"
            )
            risk += 0.9
            logger.error("Multi-agent loop detected for task '%s' in session '%s'",
                         message.task, message.session_id)

        # 4. Hop limit (prevent deep forwarding chains)
        if message.hops > MAX_LOOP_CYCLES:
            violations.append(f"Message hop limit exceeded ({message.hops} hops)")
            risk += 0.6

        # 5. Log the communication for monitoring
        self._message_log[message.session_id].append({
            "sender":   message.sender,
            "receiver": message.receiver,
            "task":     message.task,
            "ts":       message.timestamp,
        })

        risk = min(risk, 1.0)
        if violations:
            logger.warning("Multi-agent guardrail violations: %s", violations)

        return MultiAgentGuardrailResult(
            passed=len(violations) == 0,
            violations=violations,
            risk_score=risk,
        )

    # ------------------------------------------------------------------
    # Output verification between agents
    # ------------------------------------------------------------------

    def verify_cross_agent_output(
        self,
        sender: AgentRole,
        output: str,
    ) -> MultiAgentGuardrailResult:
        """Ensure an agent's output is within its expected domain."""
        violations: List[str] = []
        risk = 0.0

        # Safety agent must always agree before medical/clinical content passes
        if sender != AgentRole.SAFETY_AGENT and self._looks_medical(output):
            violations.append(
                "Medical or clinical content detected in output from "
                f"'{sender}' – must be verified by safety_agent first"
            )
            risk += 0.5

        return MultiAgentGuardrailResult(
            passed=len(violations) == 0,
            violations=violations,
            risk_score=risk,
        )

    # ------------------------------------------------------------------
    # Conflict resolution
    # ------------------------------------------------------------------

    def resolve_conflict(
        self,
        outputs: Dict[AgentRole, str],
    ) -> tuple[AgentRole, str]:
        """When multiple agents produce conflicting outputs, prefer safety_agent."""
        if AgentRole.SAFETY_AGENT in outputs:
            logger.info("Multi-agent conflict resolved: deferring to safety_agent")
            return AgentRole.SAFETY_AGENT, outputs[AgentRole.SAFETY_AGENT]
        # Fall back to orchestrator
        if AgentRole.ORCHESTRATOR in outputs:
            return AgentRole.ORCHESTRATOR, outputs[AgentRole.ORCHESTRATOR]
        # Last resort: pick any
        agent, output = next(iter(outputs.items()))
        return agent, output

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def get_session_log(self, session_id: str) -> List[Dict[str, Any]]:
        return self._message_log.get(session_id, [])

    def _looks_medical(self, text: str) -> bool:
        import re
        medical_keywords = [
            r"\bdiagnos(is|e[sd]?)\b",
            r"\bprescri(be|ption)\b",
            r"\btreat(ment|ing|s)\b",
            r"\bmedication\b",
            r"\bclinical\b",
            r"\bsymptom\b",
            r"\b(mg|mcg|ml)\s*\bper\s*\b(day|kg)\b",
        ]
        return any(re.search(p, text, re.IGNORECASE) for p in medical_keywords)
