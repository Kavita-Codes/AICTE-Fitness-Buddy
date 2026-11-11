"""
src/guardrails/hitl_guardrails.py
===================================
Guardrail 7 – Human-in-the-Loop (HITL) Guardrails
Ensures human approval for critical decisions and actions.

Checks performed:
  • Human approval gate before financial transactions
  • Approval before sending emails
  • Manual verification of critical outputs
  • Escalation to human experts
  • Approval before modifying or deleting data
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("fitness_buddy")


class ApprovalStatus(str, Enum):
    PENDING   = "pending"
    APPROVED  = "approved"
    REJECTED  = "rejected"
    ESCALATED = "escalated"
    TIMED_OUT = "timed_out"


class ActionCategory(str, Enum):
    FINANCIAL_TRANSACTION = "financial_transaction"
    SEND_EMAIL            = "send_email"
    MODIFY_USER_DATA      = "modify_user_data"
    DELETE_USER_DATA      = "delete_user_data"
    CRITICAL_OUTPUT       = "critical_output"
    MEDICAL_ADVICE        = "medical_advice"
    EXPORT_DATA           = "export_data"
    AGENT_ESCALATION      = "agent_escalation"


# Categories that always require human approval
_APPROVAL_REQUIRED: set[ActionCategory] = {
    ActionCategory.FINANCIAL_TRANSACTION,
    ActionCategory.SEND_EMAIL,
    ActionCategory.MODIFY_USER_DATA,
    ActionCategory.DELETE_USER_DATA,
    ActionCategory.EXPORT_DATA,
}

# Categories that are auto-escalated to a human expert
_EXPERT_ESCALATION_REQUIRED: set[ActionCategory] = {
    ActionCategory.MEDICAL_ADVICE,
    ActionCategory.AGENT_ESCALATION,
}


@dataclass
class ApprovalRequest:
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    action_category: ActionCategory = ActionCategory.CRITICAL_OUTPUT
    action_description: str = ""
    action_payload: Optional[Dict[str, Any]] = None
    requester_id: str = ""
    created_at: float = field(default_factory=time.time)
    status: ApprovalStatus = ApprovalStatus.PENDING
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[float] = None
    escalated_to: Optional[str] = None
    notes: str = ""

    def is_expired(self, timeout_seconds: int) -> bool:
        return time.time() - self.created_at > timeout_seconds


@dataclass
class HITLGuardrailResult:
    action_allowed: bool
    request: Optional[ApprovalRequest] = None
    reason: str = ""
    needs_human_review: bool = False
    escalation_target: Optional[str] = None


class HumanInTheLoopGuardrail:
    """
    Manages human approval workflows for critical AI actions.
    In production this integrates with a notification/approval service.
    Here it provides the full approval lifecycle management.
    """

    def __init__(self) -> None:
        from src.config import get_settings
        s = get_settings()
        self._timeout = s.hitl_approval_timeout_seconds
        self._escalation_email = s.escalation_email
        self._enabled = s.enable_human_approval
        self._pending: Dict[str, ApprovalRequest] = {}

    # ------------------------------------------------------------------
    # Main gate
    # ------------------------------------------------------------------

    def check(
        self,
        action_category: ActionCategory,
        action_description: str,
        requester_id: str = "agent",
        payload: Optional[Dict[str, Any]] = None,
    ) -> HITLGuardrailResult:
        """Determine whether an action can proceed or needs human review."""

        if not self._enabled:
            logger.info("HITL guardrails disabled – allowing action: %s", action_category)
            return HITLGuardrailResult(action_allowed=True, reason="HITL disabled")

        # Expert escalation
        if action_category in _EXPERT_ESCALATION_REQUIRED:
            req = ApprovalRequest(
                action_category=action_category,
                action_description=action_description,
                action_payload=payload,
                requester_id=requester_id,
                status=ApprovalStatus.ESCALATED,
                escalated_to=self._escalation_email,
            )
            self._pending[req.request_id] = req
            logger.warning(
                "HITL: Action escalated to expert '%s' – request_id=%s",
                self._escalation_email, req.request_id,
            )
            return HITLGuardrailResult(
                action_allowed=False,
                request=req,
                reason=f"Action escalated to human expert ({self._escalation_email})",
                needs_human_review=True,
                escalation_target=self._escalation_email,
            )

        # Approval required
        if action_category in _APPROVAL_REQUIRED:
            req = ApprovalRequest(
                action_category=action_category,
                action_description=action_description,
                action_payload=payload,
                requester_id=requester_id,
                status=ApprovalStatus.PENDING,
            )
            self._pending[req.request_id] = req
            logger.info(
                "HITL: Approval required for '%s' – request_id=%s",
                action_category, req.request_id,
            )
            return HITLGuardrailResult(
                action_allowed=False,
                request=req,
                reason=f"Action '{action_category}' requires human approval (request_id={req.request_id})",
                needs_human_review=True,
            )

        # Action is permitted without approval
        return HITLGuardrailResult(
            action_allowed=True,
            reason=f"Action '{action_category}' does not require approval",
        )

    # ------------------------------------------------------------------
    # Approval lifecycle
    # ------------------------------------------------------------------

    def approve(self, request_id: str, reviewer_id: str, notes: str = "") -> bool:
        req = self._pending.get(request_id)
        if not req:
            logger.warning("HITL: Approval for unknown request_id=%s", request_id)
            return False
        if req.is_expired(self._timeout):
            req.status = ApprovalStatus.TIMED_OUT
            logger.warning("HITL: Request %s timed out before approval", request_id)
            return False
        req.status = ApprovalStatus.APPROVED
        req.reviewed_by = reviewer_id
        req.reviewed_at = time.time()
        req.notes = notes
        logger.info("HITL: Request %s APPROVED by %s", request_id, reviewer_id)
        return True

    def reject(self, request_id: str, reviewer_id: str, notes: str = "") -> bool:
        req = self._pending.get(request_id)
        if not req:
            return False
        req.status = ApprovalStatus.REJECTED
        req.reviewed_by = reviewer_id
        req.reviewed_at = time.time()
        req.notes = notes
        logger.info("HITL: Request %s REJECTED by %s", request_id, reviewer_id)
        return True

    def is_approved(self, request_id: str) -> bool:
        req = self._pending.get(request_id)
        if not req:
            return False
        if req.is_expired(self._timeout):
            req.status = ApprovalStatus.TIMED_OUT
            return False
        return req.status == ApprovalStatus.APPROVED

    def get_pending_requests(self) -> List[ApprovalRequest]:
        now = time.time()
        results = []
        for req in self._pending.values():
            if req.status == ApprovalStatus.PENDING:
                if req.is_expired(self._timeout):
                    req.status = ApprovalStatus.TIMED_OUT
                else:
                    results.append(req)
        return results
