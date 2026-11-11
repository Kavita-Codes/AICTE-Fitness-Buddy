# 🏋️ Fitness Buddy – AI-Powered Personal Fitness & Wellness Assistant

### Powered by IBM watsonx.ai · IBM Granite · IBM Cloud Lite

> **Problem Statement No. 13** | IBM University Engagement – *Exploring the Power of Agentic AI with IBM Granite and LangFlow*

[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-red?logo=streamlit)](https://streamlit.io)
[![IBM Granite](https://img.shields.io/badge/IBM_Granite-3--8b--instruct-0f62fe?logo=ibm)](https://www.ibm.com/watsonx)
[![IBM Cloud](https://img.shields.io/badge/IBM_Cloud-Lite_Free-1192e8?logo=ibmcloud)](https://cloud.ibm.com)
[![GitHub](https://img.shields.io/badge/GitHub-Kavita--Codes%2FAICTE--Fitness--Buddy-black?logo=github)](https://github.com/Kavita-Codes/AICTE-Fitness-Buddy)
[![PDF](https://img.shields.io/badge/📄_Project_Submission-PDF-dc2626?logo=adobeacrobatreader)](docs/AICTE-Fitness-Buddy-Submission.pdf)

---

## 📋 Table of Contents

- [Problem Statement](#-problem-statement)
- [Proposed Solution](#-proposed-solution)
- [Key Features](#-key-features)
- [Technology Stack](#-technology-stack)
- [Multi-Agent Architecture](#-multi-agent-architecture)
- [Guardrails Architecture](#️-guardrails-architecture)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [Environment Configuration](#-environment-configuration)
- [Running the Application](#-running-the-application)
- [API Reference](#-api-reference)
- [Role of Agentic AI](#-role-of-agentic-ai)
- [Future Scope](#-future-scope)
- [Project Submission PDF](#-project-submission-document)
- [Disclaimer](#-disclaimer)

---

## 📌 Problem Statement

**Problem Statement No. 13 – Fitness Buddy**

### The Challenge

In today's fast-paced world, many individuals struggle to maintain a healthy lifestyle due to lack of personalized guidance, time constraints, and inconsistent motivation. Traditional fitness solutions often require expensive subscriptions, in-person consultations, or rigid schedules that don't adapt to personal preferences or daily routines.

There is a growing need for an accessible, friendly, and intelligent virtual assistant that can provide on-demand fitness advice, healthy lifestyle suggestions, and basic nutrition guidance — all tailored to individual needs and available at any time.

Maintaining a healthy lifestyle has become increasingly difficult due to:
- Busy schedules and lack of personalized fitness guidance
- Limited nutritional knowledge and inconsistent motivation
- Expensive subscriptions or personal trainers that don't match individual needs
- Predefined routines that don't adapt to daily schedules

Without accessible and personalized guidance, people find it difficult to achieve their fitness goals and develop sustainable healthy habits.

### The Objective

Build an **AI-powered Fitness Buddy** that provides personalized fitness and wellness guidance through an interactive conversational assistant. The solution should:

- **Personalized Workout Plans** – Recommend home workouts based on fitness goals, experience levels, available time, and individual preferences
- **AI-Powered Fitness Assistance** – Answer fitness-related queries and provide context-aware recommendations through an interactive chatbot
- **Nutrition & Meal Recommendations** – Suggest simple, balanced, and nutritious meals based on dietary preferences and lifestyle
- **Fitness Goal Tracking** – Help users set daily fitness goals and monitor their workout and wellness progress
- **Motivation & Habit Building** – Provide daily motivational messages, fitness tips, and reminders to encourage consistency

> **Technology Requirement:** Use of IBM Cloud Lite services / IBM Granite is mandatory.

---

## 💡 Proposed Solution

Fitness Buddy is an **AI-powered fitness companion** built using **IBM watsonx.ai**, **Granite Models**, and **LangGraph** to provide personalized fitness, workout, nutrition, and wellness guidance. The system addresses common challenges in maintaining a healthy lifestyle through an intelligent, conversational, and modular architecture.

At its core, the solution uses **Retrieval-Augmented Generation (RAG)** to retrieve relevant fitness and nutritional information from reliable knowledge sources. This enables the AI assistant to generate informative, context-aware, and personalized recommendations.

The system consists of **four key specialized agents** working collaboratively:

| Agent | Role |
|---|---|
| 🏋️ **Workout Recommendation Agent** | Generates personalized home workout routines based on fitness goals, experience level, available time, and preferences |
| 🥗 **Nutrition Agent** | Suggests balanced meal ideas, healthy food options, and basic nutritional guidance |
| 🤖 **Fitness Assistant Agent** | Handles general fitness and wellness queries through conversational AI |
| 💪 **Motivation Agent** | Provides daily motivational tips, fitness inspiration, and habit-building suggestions |

The solution includes a **user-friendly dashboard** that displays workout history, daily fitness goals, completed activities, and overall progress toward personal fitness objectives.

**LangGraph** orchestrates multi-agent workflows, while **IBM watsonx.ai** and **Granite Models** power AI-driven reasoning, response generation, and personalization. The system also incorporates **input and output guardrails** to validate user queries, filter inappropriate content, and improve the safety and reliability of AI-generated responses.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 💬 **AI Chatbot** | Full conversational interface powered by IBM Granite (ibm/granite-3-8b-instruct) via watsonx.ai |
| 🏋️ **Personalised Workouts** | Beginner / Intermediate / Advanced plans for weight loss, muscle gain, flexibility, and general fitness |
| 🥗 **Nutrition Guidance** | Meal suggestions for balanced, vegetarian, vegan, and high-protein diets |
| 📊 **BMI & Calorie Calculator** | BMI calculation + Mifflin-St Jeor calorie estimation with activity multipliers |
| 💪 **Daily Motivation** | Rotating motivational messages and habit-building tips |
| 🌿 **Wellness Hub** | Sleep, hydration, and stress management guidance |
| 🛡️ **9-Layer Guardrails** | Comprehensive safety covering input, output, tool, data, security, operational, HITL, multi-agent, and ethical layers |
| 🤖 **Multi-Agent Orchestration** | Intent-based routing to specialist agents with loop detection and conflict resolution |

---

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| **LLM** | IBM Granite (`ibm/granite-3-8b-instruct`) via IBM watsonx.ai |
| **AI Platform** | IBM Cloud Lite (free tier) |
| **Multi-Agent Orchestration** | LangGraph / Custom Python orchestrator |
| **RAG** | FAISS vector database for fitness & nutrition knowledge retrieval |
| **UI** | Streamlit (6-page interactive dashboard) |
| **API Backend** | FastAPI + Uvicorn |
| **Configuration** | pydantic-settings + python-dotenv |
| **Safety** | 9 custom guardrail modules |
| **Language** | Python 3.10+ |

---

## 🤖 Multi-Agent Architecture

```
User Query
    │
    ▼
┌─────────────────────────────────────────────────┐
│           FITNESS ORCHESTRATOR                  │
│   Intent detection → routes to best agent       │
└───┬──────────┬──────────┬──────────┬────────────┘
    ▼          ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────────┐
│Workout │ │Nutri-  │ │Motiva- │ │ Wellness   │
│ Agent  │ │tion    │ │tion    │ │  Agent     │
│        │ │ Agent  │ │ Agent  │ │            │
└────┬───┘ └────┬───┘ └────┬───┘ └────┬───────┘
     └──────────┴──────────┴──────────┘
                      │
                      ▼
              ┌───────────────┐
              │ Safety Agent  │
              │ (output check)│
              └───────┬───────┘
                      │
                      ▼
               Final Response
```

### LangGraph / Orchestrator Components Used

| Component | Function |
|---|---|
| **Chat Input** | Users enter fitness queries, workout preferences, fitness goals, and dietary details |
| **IBM watsonx AI Agent** | Processes user queries using IBM Granite models to generate personalized recommendations |
| **IBM Granite Model** | `ibm/granite-3-8b-instruct` – Natural language understanding and generation |
| **Chat Output** | Displays AI-generated workout plans, meal suggestions, fitness guidance, and motivation |
| **Workout Agent** | Generates personalized workout routines |
| **Nutrition Agent** | Suggests healthy meals and nutritional guidance |
| **Fitness Assistant Agent** | Handles fitness and wellness queries |
| **Motivation Agent** | Provides daily motivation and habit-building suggestions |
| **Guardrails** | Validates inputs and filters unsafe AI responses |
| **Dashboard** | Visualizes fitness activities, completed goals, and progress |

---

## 🛡️ Guardrails Architecture

All 9 guardrail layers fire on every user message:

```
User Message
     │
     ▼
┌──────────────────────────────────────┐
│  1. INPUT GUARDRAILS                 │
│  Injection · PII redaction ·         │
│  Malicious content · Inappropriate   │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│  5. SECURITY GUARDRAILS              │
│  Jailbreak · SQL injection ·         │
│  Credential leak · Prompt injection  │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│  6. OPERATIONAL GUARDRAILS           │
│  Rate limit · Token budget ·         │
│  Iteration cap · Exponential retry   │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│  4. DATA GUARDRAILS                  │
│  PII masking before LLM ·            │
│  RBAC · DB query safety              │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│  8. MULTI-AGENT GUARDRAILS           │
│  Access control · Loop detection ·   │
│  Conflict resolution                 │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│  IBM GRANITE GENERATION              │
│  ibm/granite-3-8b-instruct           │
│  via IBM watsonx.ai (Cloud Lite)     │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│  3. TOOL GUARDRAILS                  │
│  Allowlist · Param validation ·      │
│  SQL injection in params             │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│  2. OUTPUT GUARDRAILS                │
│  Hallucination · Toxicity ·          │
│  Sensitive data · Format validation  │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│  9. ETHICAL GUARDRAILS               │
│  Bias detection · Medical disclaimer │
│  GDPR compliance · Audit trail       │
└──────────────┬───────────────────────┘
               ▼
          Safe Response
```

> **Guardrail 7 (HITL):** Fires before financial transactions, email sends, and data deletion.
> **Guardrail 8 (Multi-Agent):** Enforces communication policies between all specialist agents.

---

## 📁 Project Structure

```
AICTE-Fitness-Buddy/
├── streamlit_app.py               # Streamlit Cloud entry point
├── app.py                         # Streamlit UI – 6 pages
├── main.py                        # FastAPI backend
├── requirements.txt               # Python dependencies
├── env.example                    # Environment template (copy to .env)
│
├── .streamlit/
│   └── config.toml                # Streamlit theme (light mode, IBM colours)
│
├── src/
│   ├── config.py                  # Settings (watsonx + guardrail config)
│   ├── agents/
│   │   ├── watsonx_client.py      # IBM Granite / watsonx.ai LLM wrapper
│   │   ├── fitness_agent.py       # Core agent – 9-layer guardrail pipeline
│   │   └── orchestrator.py        # Multi-agent orchestrator
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
│   │   └── fitness_tools.py       # BMI, calories, workouts, meals
│   ├── data/
│   │   └── fitness_knowledge.py   # Static knowledge base (offline fallback)
│   └── utils/
│       └── logger.py              # Rotating + audit logger
│
├── tests/
│   └── test_guardrails.py         # Unit tests – all 9 guardrail categories
└── logs/
    ├── app.log
    └── audit.log                  # Immutable JSON audit trail
```

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/Kavita-Codes/AICTE-Fitness-Buddy.git
cd AICTE-Fitness-Buddy
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

Edit `.env` with your IBM Cloud credentials:

```ini
WATSONX_API_KEY=your_ibm_cloud_api_key
WATSONX_PROJECT_ID=your_watsonx_project_id
WATSONX_URL=https://us-south.ml.cloud.ibm.com
GRANITE_MODEL_ID=ibm/granite-3-8b-instruct
```

> 🆓 Get a **free** IBM Cloud account: https://cloud.ibm.com/registration  
> 📂 Create a watsonx.ai project: https://dataplatform.cloud.ibm.com

### 4. Run the Streamlit UI

```bash
streamlit run streamlit_app.py
```

Opens at **http://localhost:8501** with 6 pages:
- 💬 **Chat** – Full conversational AI interface
- 🏋️ **Workouts** – Personalised workout plans
- 🥗 **Nutrition** – Meal ideas, BMI & calorie calculator
- 💪 **Motivation** – Daily inspiration
- 🌿 **Wellness** – Sleep, hydration, stress tips
- 🛡️ **Guardrails** – Real-time safety dashboard

---

## ⚙️ Environment Configuration

| Variable | Default | Description |
|---|---|---|
| `WATSONX_API_KEY` | *(required)* | IBM Cloud API key |
| `WATSONX_PROJECT_ID` | *(required)* | watsonx.ai project ID |
| `WATSONX_URL` | `https://us-south.ml.cloud.ibm.com` | Regional endpoint |
| `GRANITE_MODEL_ID` | `ibm/granite-3-8b-instruct` | Granite model ID |
| `GRANITE_MAX_NEW_TOKENS` | `1024` | Max tokens per response |
| `GRANITE_TEMPERATURE` | `0.7` | Generation temperature |
| `MAX_AGENT_ITERATIONS` | `10` | Agent loop guard |
| `MAX_EXECUTION_TIME_SECONDS` | `30` | Hard execution timeout |
| `API_RATE_LIMIT_PER_MINUTE` | `60` | Sliding-window rate limit |
| `MONTHLY_TOKEN_BUDGET` | `500000` | Monthly token spend cap |
| `ENABLE_PROMPT_INJECTION_DETECTION` | `true` | Security guardrail toggle |
| `ENABLE_PII_DETECTION` | `true` | Data privacy guardrail toggle |
| `ENABLE_HUMAN_APPROVAL` | `true` | HITL guardrail toggle |
| `ENABLE_AUDIT_TRAIL` | `true` | Writes `logs/audit.log` |

---

## 🌐 Running the Application

| Command | What it does |
|---|---|
| `streamlit run streamlit_app.py` | Launch 6-page Streamlit UI on port 8501 |
| `uvicorn main:app --reload` | Launch FastAPI backend on port 8000 |
| `python main.py` | Same as above (direct entry point) |
| `pytest tests/ -v` | Run all guardrail unit tests |

### Streamlit Community Cloud Deployment

1. Go to **https://share.streamlit.io**
2. New app → Repository: `Kavita-Codes/AICTE-Fitness-Buddy` · Branch: `main` · File: `streamlit_app.py`
3. Advanced settings → Secrets → paste `WATSONX_API_KEY`, `WATSONX_PROJECT_ID`, etc.
4. Click **Deploy**

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check |
| `GET` | `/health` | Detailed health + guardrail status |
| `POST` | `/chat` | Chat with Fitness Buddy (IBM Granite) |
| `POST` | `/reset` | Reset conversation history |
| `POST` | `/workout` | Get a personalised workout plan |
| `POST` | `/meal` | Get meal suggestions |
| `GET` | `/motivation` | Daily motivational message |
| `GET` | `/wellness/{topic}` | Wellness tips (sleep/hydration/stress) |
| `POST` | `/calculate/bmi` | BMI calculator |
| `POST` | `/calculate/calories` | Calorie estimator (Mifflin-St Jeor) |
| `GET` | `/guardrails/status` | Active guardrail configuration |

---

## 🧠 Role of Agentic AI

Agentic AI enables Fitness Buddy to function as an **intelligent, goal-oriented virtual fitness assistant** rather than a simple chatbot. Using **IBM watsonx.ai** and **IBM Granite** models, it coordinates multiple specialized agents to provide personalized fitness and wellness guidance.

Each agent performs a specific role — generating workout routines, suggesting healthy meals, answering fitness-related queries, and providing motivational guidance — while working collaboratively. This **multi-agent approach** enables efficient task execution and personalized recommendations.

Key capabilities of Agentic AI in this solution:

- **Context Awareness** – Understands user details such as fitness goals, experience levels, dietary preferences, available time, and daily routines to generate relevant suggestions
- **Adaptive Recommendations** – Modifies workout and wellness suggestions based on user preferences and feedback
- **Collaborative Agents** – Agents work together to provide comprehensive fitness guidance and help users make informed lifestyle decisions
- **Automated Task Coordination** – Intelligent decision-making and routing makes Fitness Buddy interactive, personalized, and goal-driven

> Overall, Agentic AI transforms Fitness Buddy into a **smart digital fitness companion** that helps users maintain consistency, achieve fitness goals, and develop healthier lifestyle habits.

### Token Usage

- IBM Granite model: `ibm/granite-3-8b-instruct`
- Recorded usage during development: **11,761 tokens**
- Configurable monthly budget via `MONTHLY_TOKEN_BUDGET` environment variable

---

## 🔮 Future Scope

1. **Integration with Wearables & Fitness Devices**  
   Integrate with smartwatches and fitness trackers to collect real-time data (steps, calories burned, heart rate, sleep patterns) for more accurate personalized recommendations.

2. **AI-Powered Voice Assistant & Multilingual Support**  
   Enhance with voice-enabled interaction and support for multiple languages to improve accessibility and make Fitness Buddy more inclusive.

3. **Personalized Goal Tracking & Smart Notifications**  
   Introduce automated reminders, daily challenges, and personalized notifications to encourage consistency and help users achieve fitness goals.

4. **Advanced RAG with Expanded Knowledge Base**  
   Expand the FAISS vector database with certified fitness and nutrition content from medical and sports science sources for more accurate and evidence-based recommendations.

5. **Social Features & Community Challenges**  
   Add community workout challenges, leaderboards, and social sharing to enhance motivation through peer accountability.

---

## 🔗 GitHub Repository

**https://github.com/Kavita-Codes/AICTE-Fitness-Buddy**

## 📄 Project Submission Document

> Click below to open the full IBM University Engagement project submission PDF:

### [📄 Open Project Submission PDF](docs/AICTE-Fitness-Buddy-Submission.pdf)

| Document | Link |
|---|---|
| 📋 Project Submission (PDF) | [AICTE-Fitness-Buddy-Submission.pdf](docs/AICTE-Fitness-Buddy-Submission.pdf) |

---

## ⚠️ Disclaimer

**Fitness Buddy is a supportive virtual wellness companion powered by IBM Granite (IBM Cloud Lite) and is not a substitute for qualified healthcare professionals, registered dietitians, or certified fitness trainers.** Always consult a qualified professional before beginning any new exercise programme or making significant dietary changes. The information provided is for general wellness and fitness purposes only.

---

*Built with ❤️ by **Kavita Chauhan** · IBM University Engagement Program*  
*Powered by Python · Streamlit · FastAPI · IBM watsonx.ai · IBM Granite · IBM Cloud Lite*
