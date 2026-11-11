# 🏋️ Fitness Buddy – AI-Powered Personal Fitness & Wellness Assistant
### Powered by IBM watsonx.ai · IBM Granite · IBM Cloud Lite

> A production-ready, guardrail-hardened AI fitness companion built with **Streamlit**, **FastAPI**, **IBM Granite (ibm/granite-3-8b-instruct)**, and 9 comprehensive safety guardrails.

---

## Table of Contents
- [Problem Statement](#problem-statement)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Guardrails Architecture](#guardrails-architecture)
- [Quick Start](#quick-start)
- [Environment Configuration](#environment-configuration)
- [Running the Application](#running-the-application)
- [API Reference](#api-reference)
- [Running Tests](#running-tests)
- [Disclaimer](#disclaimer)

---

## Problem Statement

In today's fast-paced world, many individuals struggle to maintain a healthy lifestyle due to lack of personalised guidance, time constraints, and inconsistent motivation. Traditional fitness solutions require expensive subscriptions, in-person consultations, or rigid schedules that don't adapt to personal preferences.

**Fitness Buddy** solves this by delivering a conversational, AI-powered health and fitness coach that can:
- Recommend home workouts and routines based on user input
- Provide motivational tips and daily fitness inspiration
- Suggest simple, nutritious meal ideas
- Encourage habit-building and consistency

---

## Key Features

| Feature | Description |
|---|---|
| 💬 **AI Chatbot** | Conversational interface powered by IBM Granite via watsonx.ai |
| 🏋️ **Personalised Workouts** | Beginner / Intermediate / Advanced plans for all goals |
| 🥗 **Nutrition Guidance** | Meal suggestions, BMI calculator, calorie estimator |
| 💪 **Daily Motivation** | Rotating messages and habit-building tips |
| 🌿 **Wellness Hub** | Sleep, hydration, and stress management guidance |
| 🛡️ **9-Layer Guardrails** | Comprehensive safety across input, output, tool, data, security, operational, HITL, multi-agent, and ethical layers |

---

## Technology Stack

| Component | Technology |
|---|---|
| **LLM** | IBM Granite (`ibm/granite-3-8b-instruct`) via IBM watsonx.ai |
| **AI Platform** | IBM Cloud Lite (free tier) |
| **UI** | Streamlit (6-page app) |
| **API Backend** | FastAPI + Uvicorn |
| **Configuration** | pydantic-settings + python-dotenv |
| **Safety** | 9 custom guardrail modules |
| **Language** | Python 3.10+ |

---

## Project Structure

```
AICTE Fitness Buddy/
├── app.py                         # Streamlit UI (6 pages) – run with: streamlit run app.py
├── main.py                        # FastAPI backend – run with: uvicorn main:app --reload
├── requirements.txt
├── env.example                    # Template – copy to .env
│
├── src/
│   ├── config.py                  # pydantic-settings config (watsonx, guardrails)
│   ├── agents/
│   │   ├── watsonx_client.py      # IBM Granite / watsonx.ai LLM wrapper
│   │   ├── fitness_agent.py       # Core agent – full 9-layer guardrail pipeline
│   │   └── orchestrator.py        # Multi-agent orchestrator (routes to specialist agents)
│   ├── guardrails/
│   │   ├── input_guardrails.py    # 1 – Input validation
│   │   ├── output_guardrails.py   # 2 – Output validation
│   │   ├── tool_guardrails.py     # 3 – Tool execution control
│   │   ├── data_guardrails.py     # 4 – Data privacy & RBAC
│   │   ├── security_guardrails.py # 5 – Security threats
│   │   ├── operational_guardrails.py  # 6 – Rate limits & budgets
│   │   ├── hitl_guardrails.py     # 7 – Human-in-the-loop
│   │   ├── multi_agent_guardrails.py  # 8 – Multi-agent safety
│   │   └── ethical_guardrails.py  # 9 – Bias, compliance, audit
│   ├── tools/
│   │   └── fitness_tools.py       # Tool functions (BMI, calories, workouts, meals…)
│   ├── data/
│   │   └── fitness_knowledge.py   # Static knowledge base (offline fallback)
│   └── utils/
│       └── logger.py              # Rotating + audit logger
│
├── tests/
│   └── test_guardrails.py         # Unit tests for all 9 guardrail categories
└── logs/
    ├── app.log
    └── audit.log
```

---

## Guardrails Architecture

```
User Message
     │
     ▼
┌──────────────────────────────────┐
│  1. INPUT GUARDRAILS             │  → PII redaction, injection detection,
│     (InputGuardrail)             │    malicious content, inappropriate filter
└───────────────┬──────────────────┘
                ▼
┌──────────────────────────────────┐
│  5. SECURITY GUARDRAILS          │  → Jailbreak, SQL injection,
│     (SecurityGuardrail)          │    credential leak, prompt injection
└───────────────┬──────────────────┘
                ▼
┌──────────────────────────────────┐
│  6. OPERATIONAL GUARDRAILS       │  → Rate limit, token budget,
│     (OperationalGuardrail)       │    iteration cap, exponential retry
└───────────────┬──────────────────┘
                ▼
┌──────────────────────────────────┐
│  4. DATA GUARDRAILS              │  → PII masking before LLM,
│     (DataGuardrail)              │    RBAC, DB query safety
└───────────────┬──────────────────┘
                ▼
┌──────────────────────────────────┐
│  8. MULTI-AGENT ORCHESTRATION    │  → Intent routing to specialist agent,
│     (FitnessOrchestrator)        │    loop detection, access control
└───────────────┬──────────────────┘
                ▼
┌──────────────────────────────────┐
│  IBM GRANITE GENERATION          │  → ibm/granite-3-8b-instruct
│  (WatsonxClient)                 │    via IBM watsonx.ai (Cloud Lite)
└───────────────┬──────────────────┘
                ▼
┌──────────────────────────────────┐
│  3. TOOL GUARDRAILS              │  → Allowlist, param validation,
│     (ToolGuardrail)              │    SQL injection in params
└───────────────┬──────────────────┘
                ▼
┌──────────────────────────────────┐
│  2. OUTPUT GUARDRAILS            │  → Hallucination, toxicity,
│     (OutputGuardrail)            │    sensitive data, format validation
└───────────────┬──────────────────┘
                ▼
┌──────────────────────────────────┐
│  9. ETHICAL GUARDRAILS           │  → Bias, medical disclaimer,
│     (EthicalGuardrail)           │    GDPR compliance, audit trail
└───────────────┬──────────────────┘
                ▼
           Safe Response
```

> **HITL (Guardrail 7)** fires for financial transactions, email sends, and data deletion.
> **Multi-Agent (Guardrail 8)** enforces communication policies between workout, nutrition, motivation, wellness, and safety agents.

---

## Quick Start

### 1. Clone / open the project

```
cd "AICTE Fitness Buddy"
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure IBM watsonx.ai credentials

```bash
# Windows
copy env.example .env

# macOS / Linux
cp env.example .env
```

Edit `.env`:
```ini
WATSONX_API_KEY=your_ibm_cloud_api_key
WATSONX_PROJECT_ID=your_project_id
WATSONX_URL=https://us-south.ml.cloud.ibm.com
GRANITE_MODEL_ID=ibm/granite-3-8b-instruct
```

> Get a **free** IBM Cloud account at https://cloud.ibm.com/registration  
> Create a watsonx.ai project at https://dataplatform.cloud.ibm.com

### 4. Run the Streamlit UI *(recommended)*

```bash
streamlit run app.py
```

Opens at **http://localhost:8501**

### 5. Run the FastAPI backend *(optional)*

```bash
uvicorn main:app --reload --port 8000
```

Swagger UI: **http://localhost:8000/docs**

---

## Environment Configuration

| Variable | Default | Description |
|---|---|---|
| `WATSONX_API_KEY` | *(required)* | IBM Cloud API key |
| `WATSONX_PROJECT_ID` | *(required)* | watsonx.ai project ID |
| `WATSONX_URL` | `https://us-south.ml.cloud.ibm.com` | Regional endpoint |
| `GRANITE_MODEL_ID` | `ibm/granite-3-8b-instruct` | Granite model ID |
| `GRANITE_MAX_NEW_TOKENS` | `1024` | Max tokens per response |
| `GRANITE_TEMPERATURE` | `0.7` | Generation temperature |
| `MAX_AGENT_ITERATIONS` | `10` | Loop guard |
| `MAX_EXECUTION_TIME_SECONDS` | `30` | Hard timeout |
| `API_RATE_LIMIT_PER_MINUTE` | `60` | Sliding-window rate limit |
| `MONTHLY_TOKEN_BUDGET` | `500000` | Monthly spend cap |
| `ENABLE_PROMPT_INJECTION_DETECTION` | `true` | Security guardrail toggle |
| `ENABLE_PII_DETECTION` | `true` | Data guardrail toggle |
| `ENABLE_HUMAN_APPROVAL` | `true` | HITL guardrail toggle |
| `ENABLE_AUDIT_TRAIL` | `true` | Writes `logs/audit.log` |

See [`env.example`](env.example) for the full list.

---

## Running the Application

| Command | What it does |
|---|---|
| `streamlit run app.py` | Launch 6-page Streamlit UI on port 8501 |
| `uvicorn main:app --reload` | Launch FastAPI backend on port 8000 |
| `python main.py` | Same as above (direct entry point) |

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check |
| `GET` | `/health` | Detailed health + guardrail status |
| `POST` | `/chat` | Chat with Fitness Buddy (Granite) |
| `POST` | `/reset` | Reset conversation history |
| `POST` | `/workout` | Get a workout plan |
| `POST` | `/meal` | Get meal suggestions |
| `GET` | `/motivation` | Daily motivational message |
| `GET` | `/wellness/{topic}` | Wellness tips |
| `POST` | `/calculate/bmi` | BMI calculator |
| `POST` | `/calculate/calories` | Calorie estimator |
| `GET` | `/guardrails/status` | Active guardrail configuration |

---

## Running Tests

```bash
pytest tests/ -v
```

Tests cover all 9 guardrail categories.

---

## Disclaimer

**Fitness Buddy is a supportive virtual wellness companion powered by IBM Granite and is not a substitute for qualified healthcare professionals, registered dietitians, or certified fitness trainers.** Always consult a qualified professional before beginning any new exercise programme or making significant dietary changes.

---

*Built with ❤️ using Python · Streamlit · FastAPI · IBM watsonx.ai · IBM Granite · IBM Cloud Lite*
