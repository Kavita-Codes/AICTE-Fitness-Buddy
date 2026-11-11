"""
src/agents/fitness_agent.py
==============================
Core AI agent for Fitness Buddy – IBM watsonx.ai / Granite edition.

Pipeline per user request:
  ① Input Guardrails    – validate / sanitise
  ② Security Guardrails – detect injection / jailbreak
  ③ Operational Guardrails – rate limit / token budget / iteration limit
  ④ Data Guardrails     – mask PII before sending to Granite
  ⑤ Granite generation  – IBM watsonx.ai (ibm/granite-3-8b-instruct)
  ⑥ Tool execution      – with Tool Guardrails
  ⑦ Output Guardrails   – filter / validate Granite response
  ⑧ Ethical Guardrails  – bias check, disclaimer, audit trail
  ⑨ Return safe response to caller
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from src.config import get_settings
from src.guardrails.data_guardrails import DataGuardrail, UserRole
from src.guardrails.ethical_guardrails import EthicalGuardrail
from src.guardrails.input_guardrails import InputGuardrail
from src.guardrails.operational_guardrails import ExecutionContext, OperationalGuardrail
from src.guardrails.output_guardrails import OutputGuardrail
from src.guardrails.security_guardrails import SecurityGuardrail
from src.guardrails.tool_guardrails import ToolGuardrail
from src.tools.fitness_tools import TOOL_REGISTRY
from src.utils.logger import setup_logger

logger = setup_logger("fitness_buddy.agent")

# ---------------------------------------------------------------------------
# System prompt for Granite instruct
# ---------------------------------------------------------------------------
_SYSTEM_PROMPT = """You are Fitness Buddy, an AI-powered personal fitness and wellness assistant powered by IBM Granite.

Your responsibilities:
1. Provide personalised workout recommendations (home workouts, equipment-free).
2. Suggest balanced, nutritious meal ideas aligned with user dietary preferences.
3. Offer daily motivation and habit-building tips.
4. Provide general wellness guidance on sleep, hydration, and stress management.
5. Answer fitness and health questions in a friendly, encouraging, inclusive tone.

Rules you MUST always follow:
- You are a supportive wellness companion, NOT a medical professional.
- Always recommend consulting a qualified healthcare provider for medical concerns.
- Provide evidence-based, safe advice. Never make exaggerated or unverified claims.
- Be inclusive and supportive for all fitness levels, body types, and backgrounds.
- Keep responses clear, practical, and actionable.
- Add a safety disclaimer whenever your response touches on medical or clinical topics.
- Powered by IBM watsonx.ai and IBM Granite language models (IBM Cloud Lite)."""


class FitnessAgent:
    """
    Orchestrates the 9-layer guardrail pipeline with IBM Granite (watsonx.ai)
    as the language model. Falls back to the static knowledge base when
    credentials are not configured.
    """

    def __init__(self, user_role: UserRole = UserRole.USER) -> None:
        from src.agents.watsonx_client import WatsonxClient

        self._settings = get_settings()
        self._user_role = user_role
        self._watsonx = WatsonxClient()

        # Initialise all 9 guardrails
        self._input_guard    = InputGuardrail()
        self._security_guard = SecurityGuardrail(secret_key=self._settings.app_secret_key)
        self._op_guard       = OperationalGuardrail()
        self._data_guard     = DataGuardrail()
        self._output_guard   = OutputGuardrail()
        self._tool_guard     = ToolGuardrail()
        self._ethical_guard  = EthicalGuardrail()

        self._conversation_history: List[Dict[str, str]] = [
            {"role": "system", "content": _SYSTEM_PROMPT}
        ]

        mode = "IBM Granite (watsonx.ai)" if self._watsonx.is_available else "knowledge-base fallback"
        logger.info("FitnessAgent initialised – mode: %s", mode)

    # ------------------------------------------------------------------
    # Public: chat
    # ------------------------------------------------------------------

    def chat(
        self,
        user_message: str,
        session_id: Optional[str] = None,
        user_id: str = "anonymous",
    ) -> Dict[str, Any]:
        """
        Process a user message through the full 9-layer guardrail pipeline
        and return a structured response dict.
        """
        session_id = session_id or str(uuid.uuid4())
        ctx = ExecutionContext(session_id=session_id, user_id=user_id)
        guardrails_triggered: List[str] = []

        # ── ① Input Guardrails ─────────────────────────────────────────
        input_result = self._input_guard.validate(user_message)
        if not input_result.passed:
            guardrails_triggered.append("input_guardrail")
            return self._blocked_response(
                reason="Your message was blocked by input safety filters.",
                details=input_result.violations,
                session_id=session_id,
                guardrails_triggered=guardrails_triggered,
            )
        clean_message = input_result.sanitized_text or user_message

        # ── ② Security Guardrails ──────────────────────────────────────
        if self._settings.enable_prompt_injection_detection:
            sec_result = self._security_guard.validate(clean_message)
            if not sec_result.passed:
                guardrails_triggered.append("security_guardrail")
                return self._blocked_response(
                    reason="Security threat detected in your message.",
                    details=sec_result.violations,
                    session_id=session_id,
                    guardrails_triggered=guardrails_triggered,
                )

        # ── ③ Operational Guardrails (rate limit + iterations) ─────────
        rate_result = self._op_guard.check_rate_limit(user_id)
        if not rate_result.passed:
            guardrails_triggered.append("rate_limit_guardrail")
            return self._blocked_response(
                reason=rate_result.reason or "Rate limit exceeded. Please wait before sending more messages.",
                details=[],
                session_id=session_id,
                guardrails_triggered=guardrails_triggered,
            )

        iter_result = self._op_guard.tick_iteration(ctx)
        if not iter_result.passed:
            guardrails_triggered.append("iteration_guardrail")
            return self._blocked_response(
                reason=iter_result.reason or "Agent iteration limit reached.",
                details=[],
                session_id=session_id,
                guardrails_triggered=guardrails_triggered,
            )

        # ── ④ Data Guardrails (PII masking before Granite) ────────────
        if self._settings.enable_pii_detection:
            data_result = self._data_guard.validate(clean_message, user_role=self._user_role)
            if isinstance(data_result.masked_data, str):
                clean_message = data_result.masked_data
            if data_result.violations:
                guardrails_triggered.append("data_guardrail")

        # ── ⑤ Granite / knowledge-base response ───────────────────────
        self._conversation_history.append({"role": "user", "content": clean_message})
        raw_response, tokens_used = self._generate_response(clean_message, ctx)
        self._op_guard.record_token_usage(tokens_used, model=self._settings.granite_model_id)
        ctx.tokens_used += tokens_used

        # ── ⑥ Tool execution ───────────────────────────────────────────
        tool_result_text = self._maybe_execute_tool(clean_message, user_id=user_id)
        if tool_result_text:
            guardrails_triggered.append("tool_guardrail")
            raw_response = raw_response + "\n\n" + tool_result_text

        # ── ⑦ Output Guardrails ────────────────────────────────────────
        if self._settings.enable_toxicity_filter or self._settings.enable_hallucination_detection:
            output_result = self._output_guard.validate(raw_response)
            if not output_result.passed:
                guardrails_triggered.append("output_guardrail")
                raw_response = output_result.filtered_text or raw_response
            elif output_result.filtered_text:
                raw_response = output_result.filtered_text

        # ── ⑧ Ethical Guardrails ───────────────────────────────────────
        ethical_result = self._ethical_guard.validate(
            text=raw_response,
            session_id=session_id,
            user_id=user_id,
            input_text=user_message,
            guardrails_triggered=guardrails_triggered,
        )
        final_response = ethical_result.enriched_text or raw_response
        if ethical_result.violations:
            guardrails_triggered.append("ethical_guardrail")

        # Add assistant turn to history
        self._conversation_history.append({"role": "assistant", "content": final_response})

        return {
            "response": final_response,
            "session_id": session_id,
            "tokens_used": tokens_used,
            "guardrails_triggered": guardrails_triggered,
            "warnings": ethical_result.warnings,
            "risk_score": max(input_result.risk_score, ethical_result.risk_score),
            "status": "success",
            "model": self._settings.granite_model_id if self._watsonx.is_available else "knowledge-base",
            "powered_by": "IBM watsonx.ai (Granite)" if self._watsonx.is_available else "Offline Knowledge Base",
        }

    # ------------------------------------------------------------------
    # LLM / Knowledge-base generation
    # ------------------------------------------------------------------

    def _generate_response(self, message: str, ctx: ExecutionContext) -> tuple[str, int]:
        """Call IBM Granite or fall back to knowledge base."""
        # Token budget check
        token_check = self._op_guard.check_token_limit(self._settings.max_tokens_per_request, ctx)
        if not token_check.passed:
            return self._knowledge_base_response(message), 0

        if self._watsonx.is_available:
            try:
                text, tokens = self._watsonx.generate_with_messages(self._conversation_history)
                if text:
                    self._op_guard.reset_failure_count(ctx.session_id)
                    return text, tokens
            except Exception as exc:
                retry = self._op_guard.should_retry(ctx.session_id, exc)
                if retry.should_retry:
                    logger.info("Retrying Granite call after %.1fs", retry.retry_after_seconds)
                    time.sleep(retry.retry_after_seconds)
                    try:
                        text, tokens = self._watsonx.generate_with_messages(self._conversation_history)
                        if text:
                            return text, tokens
                    except Exception:
                        pass
                logger.warning("Granite unavailable – falling back to knowledge base")

        return self._knowledge_base_response(message), 0

    def _knowledge_base_response(self, message: str) -> str:
        """Rule-based fallback when Granite / watsonx.ai is unavailable."""
        msg_lower = message.lower()
        from src.tools.fitness_tools import (
            get_meal_suggestion,
            get_motivation_message,
            get_wellness_guidance,
            get_workout_plan,
        )

        if any(w in msg_lower for w in ["workout", "exercise", "training", "routine", "gym"]):
            plan = get_workout_plan()
            exercises = "\n".join(f"  • {e}" for e in plan["exercises"])
            return (
                f"Here's a workout plan tailored for you:\n\n{exercises}\n\n"
                f"💡 {plan['tip']}\n\n"
                f"*Powered by Fitness Buddy knowledge base*"
            )
        if any(w in msg_lower for w in ["meal", "eat", "food", "diet", "nutrition", "recipe"]):
            result = get_meal_suggestion()
            meals = "\n".join(
                f"  • {m['name']} ({m['calories']}, Protein: {m['protein']})"
                for m in result["meal_suggestions"]
            )
            return (
                f"Here are some healthy meal ideas:\n\n{meals}\n\n"
                f"💧 {result['hydration_reminder']}\n\n"
                f"*Powered by Fitness Buddy knowledge base*"
            )
        if any(w in msg_lower for w in ["motivat", "inspire", "encourage", "tip"]):
            result = get_motivation_message()
            return f"{result['message']}\n\n🎯 Daily Goal: {result['daily_goal']}"

        if any(w in msg_lower for w in ["sleep", "rest", "recover"]):
            result = get_wellness_guidance("sleep")
            tips = "\n".join(f"  • {t}" for t in result["tips"])
            return f"**Sleep & Recovery Tips:**\n\n{tips}"

        if any(w in msg_lower for w in ["water", "hydrat", "drink"]):
            result = get_wellness_guidance("hydration")
            tips = "\n".join(f"  • {t}" for t in result["tips"])
            return f"**Hydration Tips:**\n\n{tips}"

        if any(w in msg_lower for w in ["stress", "mental", "relax", "anxiety"]):
            result = get_wellness_guidance("stress")
            tips = "\n".join(f"  • {t}" for t in result["tips"])
            return f"**Stress & Mental Wellness Tips:**\n\n{tips}"

        result = get_motivation_message()
        return (
            f"👋 Hi there! I'm **Fitness Buddy**, your AI-powered wellness companion "
            f"(IBM Granite – offline mode).\n\n"
            f"I can help you with:\n"
            f"  🏋️ **Workouts** – home routines for all levels\n"
            f"  🥗 **Nutrition** – healthy meal ideas\n"
            f"  💪 **Motivation** – daily inspiration\n"
            f"  🌿 **Wellness** – sleep, hydration, stress tips\n\n"
            f"✨ {result['message']}"
        )

    # ------------------------------------------------------------------
    # Tool execution
    # ------------------------------------------------------------------

    def _maybe_execute_tool(self, message: str, user_id: str = "user") -> Optional[str]:
        """Keyword-detect tool calls and execute them through the tool guardrail."""
        import re
        msg_lower = message.lower()

        tool_name: Optional[str] = None
        params: Dict[str, Any] = {}

        if "bmi" in msg_lower:
            weight_match = re.search(r"(\d+(?:\.\d+)?)\s*kg", msg_lower)
            height_match = re.search(r"(\d+(?:\.\d+)?)\s*m(?:eter|etres?)?(?!\w)", msg_lower)
            if weight_match and height_match:
                tool_name = "calculate_bmi"
                params = {
                    "weight_kg": float(weight_match.group(1)),
                    "height_m": float(height_match.group(1)),
                }
            else:
                return None

        elif any(w in msg_lower for w in ["calorie", "tdee", "bmr", "caloric need"]):
            w = re.search(r"(\d+(?:\.\d+)?)\s*kg", msg_lower)
            h = re.search(r"(\d+(?:\.\d+)?)\s*m(?:eter|etres?)?(?!\w)", msg_lower)
            a = re.search(r"(\d+)\s*(?:years?\s*old|yr)", msg_lower)
            if w and h and a:
                tool_name = "calculate_calories"
                params = {
                    "weight_kg": float(w.group(1)),
                    "height_m": float(h.group(1)),
                    "age": int(a.group(1)),
                    "activity_level": "moderate",
                }
            else:
                return None

        if not tool_name:
            return None

        guard_result = self._tool_guard.validate(tool_name, params, caller_id=user_id)
        if not guard_result.passed:
            logger.warning("Tool '%s' blocked: %s", tool_name, guard_result.violations)
            return None

        tool_fn = TOOL_REGISTRY.get(tool_name)
        if not tool_fn:
            return None

        try:
            result = tool_fn(**params)
            return self._format_tool_result(tool_name, result)
        except Exception as exc:
            logger.error("Tool execution error '%s': %s", tool_name, exc)
            return None

    def _format_tool_result(self, tool_name: str, result: Dict[str, Any]) -> str:
        if tool_name == "calculate_bmi":
            return (
                f"📊 **BMI Calculation:**\n"
                f"  • BMI: **{result.get('bmi')}** ({result.get('category')})\n"
                f"  • Advice: {result.get('advice')}\n"
                f"  ⚠️ *{result.get('disclaimer')}*"
            )
        if tool_name == "calculate_calories":
            return (
                f"🔥 **Daily Calorie Estimate (Mifflin-St Jeor):**\n"
                f"  • BMR: {result.get('bmr')} kcal/day\n"
                f"  • TDEE (maintenance): **{result.get('tdee')} kcal/day**\n"
                f"  • For weight loss: {result.get('for_weight_loss')} kcal/day\n"
                f"  • For muscle gain: {result.get('for_weight_gain')} kcal/day\n"
                f"  📝 *{result.get('note')}*"
            )
        return str(result)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _blocked_response(
        self,
        reason: str,
        details: List[str],
        session_id: str,
        guardrails_triggered: List[str],
    ) -> Dict[str, Any]:
        self._ethical_guard.write_custom_audit(
            "blocked_request",
            {"session_id": session_id, "reason": reason, "details": details},
        )
        return {
            "response": (
                f"⚠️ {reason}\n\n"
                "Please rephrase your message and try again."
            ),
            "session_id": session_id,
            "tokens_used": 0,
            "guardrails_triggered": guardrails_triggered,
            "warnings": details,
            "risk_score": 1.0,
            "status": "blocked",
            "model": "guardrail",
            "powered_by": "IBM Fitness Buddy Guardrails",
        }

    def reset_conversation(self) -> None:
        """Clear conversation history (keep system prompt)."""
        self._conversation_history = [{"role": "system", "content": _SYSTEM_PROMPT}]
        logger.info("Conversation history reset")

    @property
    def is_granite_active(self) -> bool:
        return self._watsonx.is_available
