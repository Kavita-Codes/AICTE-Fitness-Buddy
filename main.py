"""
main.py – Fitness Buddy FastAPI Application
IBM watsonx.ai / Granite (IBM Cloud Lite) Edition

Run: uvicorn main:app --reload --port 8000
     python main.py
"""

from __future__ import annotations

import sys
import uuid
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.agents.orchestrator import FitnessOrchestrator
from src.config import get_settings
from src.utils.logger import setup_audit_logger, setup_logger

logger = setup_logger("fitness_buddy")
setup_audit_logger()
settings = get_settings()

# ---------------------------------------------------------------------------
# Application lifecycle
# ---------------------------------------------------------------------------

_orchestrator: Optional[FitnessOrchestrator] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _orchestrator
    logger.info("Starting %s …", settings.app_name)
    _orchestrator = FitnessOrchestrator()
    mode = "IBM Granite (watsonx.ai)" if _orchestrator.is_granite_active else "knowledge-base"
    logger.info("LLM mode: %s", mode)
    yield
    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    description=(
        "AI-Powered Personal Fitness & Wellness Assistant "
        "– IBM watsonx.ai / Granite (IBM Cloud Lite)"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    user_id: str = "anonymous"
    user_role: str = "user"


class ChatResponse(BaseModel):
    response: str
    session_id: str
    status: str
    agent: Optional[str] = None
    tokens_used: int = 0
    guardrails_triggered: List[str] = []
    warnings: List[str] = []
    risk_score: float = 0.0
    powered_by: str = ""


class WorkoutRequest(BaseModel):
    fitness_goal: str = "general_fitness"
    experience_level: str = "beginner"


class MealRequest(BaseModel):
    dietary_preference: str = "balanced"


class BMIRequest(BaseModel):
    weight_kg: float = Field(..., gt=0, le=500)
    height_m: float = Field(..., gt=0, le=3.0)


class CalorieRequest(BaseModel):
    weight_kg: float = Field(..., gt=0, le=500)
    height_m: float = Field(..., gt=0, le=3.0)
    age: int = Field(..., ge=10, le=120)
    activity_level: str = "moderate"
    sex: str = "male"

# ---------------------------------------------------------------------------
# Dependency helper
# ---------------------------------------------------------------------------

def get_orchestrator() -> FitnessOrchestrator:
    if _orchestrator is None:
        raise HTTPException(status_code=503, detail="Orchestrator not initialised")
    return _orchestrator


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", summary="Health check", tags=["System"])
async def root() -> Dict[str, str]:
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": "1.0.0",
        "powered_by": "IBM watsonx.ai (Granite)",
    }


@app.get("/health", summary="Detailed health check", tags=["System"])
async def health() -> Dict[str, Any]:
    from src.guardrails.operational_guardrails import OperationalGuardrail
    op = OperationalGuardrail()
    orch = get_orchestrator()
    return {
        "status": "healthy",
        "app": settings.app_name,
        "llm": {
            "provider": "IBM watsonx.ai",
            "model": settings.granite_model_id,
            "active": orch.is_granite_active,
            "url": settings.watsonx_url,
        },
        "guardrails": {
            "1_input":       True,
            "2_output":      True,
            "3_tool":        True,
            "4_data":        settings.enable_pii_detection,
            "5_security":    settings.enable_prompt_injection_detection,
            "6_operational": True,
            "7_hitl":        settings.enable_human_approval,
            "8_multi_agent": True,
            "9_ethical":     True,
        },
        "operational": op.status(),
    }


@app.post("/chat", response_model=ChatResponse, summary="Chat with Fitness Buddy", tags=["Chat"])
async def chat(request: ChatRequest) -> ChatResponse:
    orch = get_orchestrator()
    session_id = request.session_id or str(uuid.uuid4())
    result = orch.process_query(
        user_message=request.message,
        session_id=session_id,
        user_id=request.user_id,
    )
    return ChatResponse(**{k: result[k] for k in ChatResponse.model_fields if k in result})


@app.post("/reset", summary="Reset conversation history", tags=["Chat"])
async def reset_session() -> Dict[str, str]:
    get_orchestrator().reset_session()
    return {"status": "ok", "message": "Conversation reset"}


@app.post("/workout", summary="Get workout plan", tags=["Fitness"])
async def get_workout(request: WorkoutRequest) -> Dict[str, Any]:
    from src.tools.fitness_tools import get_workout_plan
    return get_workout_plan(fitness_goal=request.fitness_goal, experience_level=request.experience_level)


@app.post("/meal", summary="Get meal suggestions", tags=["Nutrition"])
async def get_meal(request: MealRequest) -> Dict[str, Any]:
    from src.tools.fitness_tools import get_meal_suggestion
    return get_meal_suggestion(dietary_preference=request.dietary_preference)


@app.get("/motivation", summary="Daily motivational message", tags=["Motivation"])
async def get_motivation() -> Dict[str, str]:
    from src.tools.fitness_tools import get_motivation_message
    return get_motivation_message()


@app.get("/wellness/{topic}", summary="Wellness tips by topic", tags=["Wellness"])
async def get_wellness(topic: str) -> Dict[str, Any]:
    from src.tools.fitness_tools import get_wellness_guidance
    return get_wellness_guidance(topic=topic)


@app.post("/calculate/bmi", summary="Calculate BMI", tags=["Calculators"])
async def calc_bmi(request: BMIRequest) -> Dict[str, Any]:
    from src.tools.fitness_tools import calculate_bmi
    return calculate_bmi(weight_kg=request.weight_kg, height_m=request.height_m)


@app.post("/calculate/calories", summary="Estimate daily calorie needs", tags=["Calculators"])
async def calc_calories(request: CalorieRequest) -> Dict[str, Any]:
    from src.tools.fitness_tools import calculate_calories
    return calculate_calories(
        weight_kg=request.weight_kg,
        height_m=request.height_m,
        age=request.age,
        activity_level=request.activity_level,
        sex=request.sex,
    )


@app.get("/guardrails/status", summary="Active guardrail configuration", tags=["System"])
async def guardrails_status() -> Dict[str, Any]:
    return {
        "guardrails": {
            "1_input":       {"enabled": True, "checks": ["injection", "malicious", "validation", "pii", "inappropriate"]},
            "2_output":      {"enabled": True, "checks": ["hallucination", "factual", "toxicity", "sensitive", "format"]},
            "3_tool":        {"enabled": True, "checks": ["allowlist", "api_auth", "param_validation", "sql_injection"]},
            "4_data":        {"enabled": settings.enable_pii_detection, "checks": ["pii_masking", "rbac", "db_validation"]},
            "5_security":    {"enabled": settings.enable_prompt_injection_detection, "checks": ["injection", "jailbreak", "sql", "credential_leak"]},
            "6_operational": {"enabled": True, "checks": ["time_limit", "token_budget", "rate_limit", "iterations", "retry"]},
            "7_hitl":        {"enabled": settings.enable_human_approval, "checks": ["financial", "email", "data_modification", "escalation"]},
            "8_multi_agent": {"enabled": True, "checks": ["access_control", "task_validation", "loop_detection", "conflict_resolution"]},
            "9_ethical":     {"enabled": True, "checks": ["bias", "fairness", "explainability", "compliance", "audit_trail"]},
        }
    }


# ---------------------------------------------------------------------------
# Global exception handler
# ---------------------------------------------------------------------------

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal error occurred. Please try again."},
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug,
    )
