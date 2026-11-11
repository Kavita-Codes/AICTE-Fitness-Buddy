"""
src/agents/watsonx_client.py
==============================
IBM watsonx.ai / Granite LLM client (IBM Cloud Lite).

Wraps the ibm-watsonx-ai SDK with:
  • IAM token management (auto-refresh)
  • Granite model invocation
  • Graceful fallback to knowledge-base when credentials are absent
  • Retry logic aligned with OperationalGuardrails
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("fitness_buddy.watsonx")


class WatsonxClient:
    """
    Thin wrapper around ibm-watsonx-ai ModelInference.
    Falls back to offline knowledge-base mode if the SDK is not installed
    or credentials are not configured.
    """

    def __init__(self) -> None:
        from src.config import get_settings
        self._settings = get_settings()
        self._model: Optional[Any] = None
        self._sdk_available = self._check_sdk()

        if self._sdk_available and self._settings.is_watsonx_configured:
            self._init_model()
        else:
            logger.info(
                "WatsonxClient: running in OFFLINE mode "
                "(SDK not installed or credentials not configured)"
            )

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _check_sdk(self) -> bool:
        try:
            import ibm_watsonx_ai  # noqa: F401
            return True
        except ImportError:
            logger.warning(
                "ibm-watsonx-ai SDK not installed. "
                "Run: pip install ibm-watsonx-ai"
            )
            return False

    def _init_model(self) -> None:
        """Initialise the Granite ModelInference object."""
        try:
            from ibm_watsonx_ai import APIClient, Credentials
            from ibm_watsonx_ai.foundation_models import ModelInference
            from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

            credentials = Credentials(
                url=self._settings.watsonx_url,
                api_key=self._settings.watsonx_api_key,
            )
            client = APIClient(credentials)

            params = self._settings.granite_params
            # Map our param names to watsonx SDK meta-names
            gen_params = {
                GenParams.MAX_NEW_TOKENS:      params["max_new_tokens"],
                GenParams.MIN_NEW_TOKENS:      params["min_new_tokens"],
                GenParams.TEMPERATURE:         params["temperature"],
                GenParams.TOP_P:               params["top_p"],
                GenParams.TOP_K:               params["top_k"],
                GenParams.REPETITION_PENALTY:  params["repetition_penalty"],
                GenParams.DECODING_METHOD:     params["decoding_method"],
            }

            self._model = ModelInference(
                model_id=self._settings.granite_model_id,
                api_client=client,
                project_id=self._settings.watsonx_project_id,
                params=gen_params,
            )
            logger.info(
                "WatsonxClient: connected to Granite model '%s' at %s",
                self._settings.granite_model_id,
                self._settings.watsonx_url,
            )
        except Exception as exc:
            logger.error("WatsonxClient: failed to initialise Granite model: %s", exc)
            self._model = None

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> tuple[str, int]:
        """
        Generate a response from Granite.
        Returns (response_text, estimated_tokens_used).
        Falls back to empty string if unavailable.
        """
        if not self._model:
            return "", 0

        full_prompt = self._build_prompt(prompt, system_prompt, conversation_history)

        try:
            response = self._model.generate_text(prompt=full_prompt)
            # ibm-watsonx-ai returns a string directly from generate_text
            text = response.strip() if isinstance(response, str) else str(response).strip()
            tokens = self._estimate_tokens(full_prompt + text)
            logger.debug("Granite generated %d estimated tokens", tokens)
            return text, tokens

        except Exception as exc:
            logger.error("Granite generation failed: %s", exc)
            return "", 0

    def generate_with_messages(
        self,
        messages: List[Dict[str, str]],
    ) -> tuple[str, int]:
        """
        Chat-style generation using a messages list
        ({"role": "system"|"user"|"assistant", "content": "..."}).
        """
        if not self._model:
            return "", 0

        system_msg = next(
            (m["content"] for m in messages if m["role"] == "system"), None
        )
        history = [m for m in messages if m["role"] != "system"]
        user_msg = history[-1]["content"] if history else ""
        prior = history[:-1]

        return self.generate(
            prompt=user_msg,
            system_prompt=system_msg,
            conversation_history=prior,
        )

    # ------------------------------------------------------------------
    # Prompt construction (Granite instruct format)
    # ------------------------------------------------------------------

    def _build_prompt(
        self,
        user_message: str,
        system_prompt: Optional[str],
        history: Optional[List[Dict[str, str]]],
    ) -> str:
        """
        Build a Granite-compatible instruct prompt.
        Granite-3 uses <|system|>, <|user|>, <|assistant|> tokens.
        """
        parts: List[str] = []

        if system_prompt:
            parts.append(f"<|system|>\n{system_prompt}\n<|end_of_text|>")

        if history:
            for msg in history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    parts.append(f"<|user|>\n{content}\n<|end_of_text|>")
                elif role == "assistant":
                    parts.append(f"<|assistant|>\n{content}\n<|end_of_text|>")

        parts.append(f"<|user|>\n{user_message}\n<|end_of_text|>")
        parts.append("<|assistant|>")

        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimate: ~4 chars per token for English."""
        return max(1, len(text) // 4)

    @property
    def is_available(self) -> bool:
        return self._model is not None

    @property
    def model_id(self) -> str:
        return self._settings.granite_model_id

    @property
    def is_online(self) -> bool:
        return self._sdk_available and self._settings.is_watsonx_configured
