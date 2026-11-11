"""
src/guardrails/operational_guardrails.py
==========================================
Guardrail 6 – Operational Guardrails
Controls agent execution time, token usage, rate limits, and cost.

Checks performed:
  • Maximum execution time enforcement
  • Token usage limits and budget tracking
  • API rate limiting (per-user and global)
  • Maximum agent iterations
  • Cost monitoring and budget limits
  • Retry and failure handling with exponential back-off
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Callable, Deque, Dict, Optional

logger = logging.getLogger("fitness_buddy")


@dataclass
class ExecutionContext:
    """Tracks live state for a single agent execution run."""
    session_id: str
    user_id: str
    start_time: float = field(default_factory=time.time)
    iteration_count: int = 0
    tokens_used: int = 0
    cost_usd: float = 0.0
    api_calls: int = 0

    def elapsed(self) -> float:
        return time.time() - self.start_time


@dataclass
class OperationalGuardrailResult:
    passed: bool
    reason: Optional[str] = None
    should_retry: bool = False
    retry_after_seconds: float = 0.0


# Cost per 1 000 tokens (approximate, USD) – update as pricing changes
_TOKEN_COST_PER_1K: Dict[str, float] = {
    "gpt-4o":              0.005,
    "gpt-4o-mini":         0.00015,
    "gpt-3.5-turbo":       0.0005,
    "gemini-1.5-flash":    0.00010,
    "gemini-1.5-pro":      0.00125,
}


class RateLimiter:
    """Sliding-window rate limiter per user or global."""

    def __init__(self, max_calls: int, window_seconds: int = 60) -> None:
        self._max_calls = max_calls
        self._window = window_seconds
        self._windows: Dict[str, Deque[float]] = defaultdict(deque)

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        dq = self._windows[key]
        # Remove entries outside the window
        while dq and dq[0] < now - self._window:
            dq.popleft()
        if len(dq) >= self._max_calls:
            return False
        dq.append(now)
        return True

    def remaining(self, key: str) -> int:
        now = time.time()
        dq = self._windows[key]
        while dq and dq[0] < now - self._window:
            dq.popleft()
        return max(0, self._max_calls - len(dq))


class OperationalGuardrail:
    """
    Enforces execution limits, token budgets, rate limits, and retry logic.
    """

    def __init__(self) -> None:
        from src.config import get_settings
        s = get_settings()

        self._max_time   = s.max_execution_time_seconds
        self._max_iter   = s.max_agent_iterations
        self._max_tokens = s.max_tokens_per_request
        self._monthly_budget = s.monthly_token_budget
        self._retry_max  = s.retry_max_attempts
        self._retry_backoff = s.retry_backoff_seconds
        self._rate_limiter = RateLimiter(s.api_rate_limit_per_minute, window_seconds=60)

        self._monthly_tokens_used: int = 0
        self._monthly_cost_usd: float = 0.0
        self._failure_counts: Dict[str, int] = defaultdict(int)

    # ------------------------------------------------------------------
    # Check methods
    # ------------------------------------------------------------------

    def check_time_limit(self, ctx: ExecutionContext) -> OperationalGuardrailResult:
        if ctx.elapsed() > self._max_time:
            msg = f"Execution time limit exceeded ({ctx.elapsed():.1f}s > {self._max_time}s)"
            logger.warning("Operational guardrail: %s [session=%s]", msg, ctx.session_id)
            return OperationalGuardrailResult(passed=False, reason=msg)
        return OperationalGuardrailResult(passed=True)

    def check_iteration_limit(self, ctx: ExecutionContext) -> OperationalGuardrailResult:
        if ctx.iteration_count >= self._max_iter:
            msg = f"Maximum agent iterations reached ({ctx.iteration_count}/{self._max_iter})"
            logger.warning("Operational guardrail: %s [session=%s]", msg, ctx.session_id)
            return OperationalGuardrailResult(passed=False, reason=msg)
        return OperationalGuardrailResult(passed=True)

    def check_token_limit(self, requested_tokens: int, ctx: ExecutionContext) -> OperationalGuardrailResult:
        if requested_tokens > self._max_tokens:
            msg = f"Token request exceeds per-request limit ({requested_tokens} > {self._max_tokens})"
            logger.warning("Operational guardrail: %s", msg)
            return OperationalGuardrailResult(passed=False, reason=msg)
        if self._monthly_tokens_used + requested_tokens > self._monthly_budget:
            msg = (
                f"Monthly token budget would be exceeded "
                f"({self._monthly_tokens_used + requested_tokens} > {self._monthly_budget})"
            )
            logger.error("Operational guardrail: %s", msg)
            return OperationalGuardrailResult(passed=False, reason=msg)
        return OperationalGuardrailResult(passed=True)

    def check_rate_limit(self, user_id: str) -> OperationalGuardrailResult:
        if not self._rate_limiter.is_allowed(user_id):
            remaining = self._rate_limiter.remaining(user_id)
            msg = f"Rate limit exceeded for user '{user_id}' (retry after 60s)"
            logger.warning("Operational guardrail: %s", msg)
            return OperationalGuardrailResult(
                passed=False, reason=msg, should_retry=True, retry_after_seconds=60.0
            )
        return OperationalGuardrailResult(passed=True)

    # ------------------------------------------------------------------
    # Token and cost accounting
    # ------------------------------------------------------------------

    def record_token_usage(self, tokens: int, model: str = "gpt-4o") -> float:
        """Update running totals; returns cost in USD for this call."""
        self._monthly_tokens_used += tokens
        cost_per_1k = _TOKEN_COST_PER_1K.get(model, 0.005)
        cost = (tokens / 1000) * cost_per_1k
        self._monthly_cost_usd += cost
        logger.debug("Token usage: +%d tokens ($%.6f) – monthly total: %d tokens ($%.4f)",
                     tokens, cost, self._monthly_tokens_used, self._monthly_cost_usd)
        return cost

    # ------------------------------------------------------------------
    # Retry logic
    # ------------------------------------------------------------------

    def should_retry(self, session_id: str, error: Exception) -> OperationalGuardrailResult:
        """Determine whether a failed call should be retried."""
        attempts = self._failure_counts[session_id]
        if attempts >= self._retry_max:
            msg = f"Max retries ({self._retry_max}) exceeded for session '{session_id}'"
            logger.error("Operational guardrail: %s", msg)
            return OperationalGuardrailResult(passed=False, reason=msg, should_retry=False)

        self._failure_counts[session_id] += 1
        wait = self._retry_backoff * (2 ** attempts)  # exponential back-off
        logger.info("Retry %d/%d for session '%s' after %.1fs (error: %s)",
                    attempts + 1, self._retry_max, session_id, wait, error)
        return OperationalGuardrailResult(
            passed=True, should_retry=True, retry_after_seconds=wait
        )

    def reset_failure_count(self, session_id: str) -> None:
        self._failure_counts.pop(session_id, None)

    # ------------------------------------------------------------------
    # Increment iteration counter
    # ------------------------------------------------------------------

    def tick_iteration(self, ctx: ExecutionContext) -> OperationalGuardrailResult:
        ctx.iteration_count += 1
        return self.check_iteration_limit(ctx)

    # ------------------------------------------------------------------
    # Status report
    # ------------------------------------------------------------------

    def status(self) -> Dict[str, Any]:
        return {
            "monthly_tokens_used": self._monthly_tokens_used,
            "monthly_budget": self._monthly_budget,
            "monthly_cost_usd": round(self._monthly_cost_usd, 4),
            "budget_remaining_pct": round(
                (1 - self._monthly_tokens_used / max(self._monthly_budget, 1)) * 100, 1
            ),
        }
