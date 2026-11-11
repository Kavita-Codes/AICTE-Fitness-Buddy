"""
src/config.py – Centralised application configuration via pydantic-settings.
IBM watsonx.ai / Granite (IBM Cloud Lite) edition.

Credential resolution order:
  1. Streamlit secrets (st.secrets) – used when deployed on Streamlit Cloud
  2. Environment variables / .env file – used locally
"""

from __future__ import annotations

import os
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _inject_streamlit_secrets() -> None:
    """
    Copy Streamlit secrets into os.environ so pydantic-settings can read them.
    Safe to call even when streamlit is not installed or secrets are not set.
    """
    try:
        import streamlit as st
        secrets = dict(st.secrets)
        for key, value in secrets.items():
            if isinstance(value, str) and key not in os.environ:
                os.environ[key.upper()] = value
    except Exception:
        pass  # Not running under Streamlit, or no secrets configured


_inject_streamlit_secrets()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────────────────────────
    app_name: str = "Fitness Buddy"
    app_env: str = "development"
    app_debug: bool = False
    app_secret_key: str = "change_me_in_production"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # ── IBM watsonx.ai / Granite (IBM Cloud Lite) ─────────────────────────────
    watsonx_api_key: str = ""
    watsonx_project_id: str = ""
    watsonx_url: str = "https://us-south.ml.cloud.ibm.com"
    ibm_cloud_iam_url: str = "https://iam.cloud.ibm.com/identity/token"

    # IBM Granite model IDs
    granite_model_id: str = "ibm/granite-3-8b-instruct"
    granite_vision_model_id: str = "ibm/granite-3-8b-instruct"

    # Granite generation parameters
    granite_max_new_tokens: int = 1024
    granite_min_new_tokens: int = 10
    granite_temperature: float = 0.7
    granite_top_p: float = 0.95
    granite_top_k: int = 50
    granite_repetition_penalty: float = 1.1
    granite_decoding_method: str = "greedy"

    # ── Operational Guardrails ────────────────────────────────────────────────
    max_tokens_per_request: int = 1024
    max_agent_iterations: int = 10
    max_execution_time_seconds: int = 30
    api_rate_limit_per_minute: int = 60
    monthly_token_budget: int = 500_000
    retry_max_attempts: int = 3
    retry_backoff_seconds: float = 2.0

    # ── Security Guardrails ───────────────────────────────────────────────────
    enable_prompt_injection_detection: bool = True
    enable_jailbreak_detection: bool = True
    enable_sql_injection_prevention: bool = True
    allowed_origins: str = "http://localhost:3000,http://localhost:8000,http://localhost:8501"

    # ── Data Guardrails ───────────────────────────────────────────────────────
    enable_pii_detection: bool = True
    enable_data_masking: bool = True
    enable_audit_trail: bool = True
    audit_log_path: str = "logs/audit.log"

    # ── Content Guardrails ────────────────────────────────────────────────────
    enable_toxicity_filter: bool = True
    enable_hallucination_detection: bool = True
    enable_factual_validation: bool = True

    # ── Human-in-the-Loop ────────────────────────────────────────────────────
    enable_human_approval: bool = True
    hitl_approval_timeout_seconds: int = 300
    escalation_email: str = "admin@fitnessbuddy.local"

    # ── Logging ───────────────────────────────────────────────────────────────
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    log_max_bytes: int = 10_485_760
    log_backup_count: int = 5

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def is_watsonx_configured(self) -> bool:
        """True when real IBM Cloud credentials are present."""
        return (
            bool(self.watsonx_api_key)
            and not self.watsonx_api_key.startswith("your_")
            and bool(self.watsonx_project_id)
            and not self.watsonx_project_id.startswith("your_")
        )

    @property
    def granite_params(self) -> dict:
        """Return a dict of Granite generation parameters."""
        return {
            "max_new_tokens": self.granite_max_new_tokens,
            "min_new_tokens": self.granite_min_new_tokens,
            "temperature": self.granite_temperature,
            "top_p": self.granite_top_p,
            "top_k": self.granite_top_k,
            "repetition_penalty": self.granite_repetition_penalty,
            "decoding_method": self.granite_decoding_method,
        }


def get_settings() -> Settings:
    """Return a Settings instance (re-reads each call to pick up Streamlit secrets)."""
    return Settings()
