"""
src/tools/fitness_tools.py
============================
Concrete tool functions the AI agents call.
Each function is a pure Python callable – no external API required
for the knowledge-base path; LLM path is used when a key is available.
"""

from __future__ import annotations

import random
from typing import Any, Dict, Optional

from src.data.fitness_knowledge import (
    MEAL_SUGGESTIONS,
    MOTIVATIONAL_MESSAGES,
    WELLNESS_TIPS,
    WORKOUT_PLANS,
)


# ---------------------------------------------------------------------------
# Tool: get_workout_plan
# ---------------------------------------------------------------------------
def get_workout_plan(fitness_goal: str = "general_fitness", experience_level: str = "beginner") -> Dict[str, Any]:
    """Return a tailored workout plan from the knowledge base."""
    goal = fitness_goal.lower().replace(" ", "_")
    level = experience_level.lower()

    plans = WORKOUT_PLANS.get(goal, WORKOUT_PLANS["general_fitness"])
    exercises = plans.get(level, plans["beginner"])

    return {
        "goal": fitness_goal,
        "experience_level": experience_level,
        "exercises": exercises,
        "tip": "Remember to warm up for 5 minutes before starting and cool down afterwards.",
    }


# ---------------------------------------------------------------------------
# Tool: get_meal_suggestion
# ---------------------------------------------------------------------------
def get_meal_suggestion(dietary_preference: str = "balanced") -> Dict[str, Any]:
    """Return meal suggestions based on dietary preference."""
    pref = dietary_preference.lower().replace(" ", "_")
    meals = MEAL_SUGGESTIONS.get(pref, MEAL_SUGGESTIONS["balanced"])
    selected = random.sample(meals, min(2, len(meals)))

    return {
        "dietary_preference": dietary_preference,
        "meal_suggestions": selected,
        "hydration_reminder": "Drink at least 2–3 litres of water today.",
    }


# ---------------------------------------------------------------------------
# Tool: get_motivation_message
# ---------------------------------------------------------------------------
def get_motivation_message() -> Dict[str, str]:
    """Return a daily motivational fitness message."""
    return {
        "message": random.choice(MOTIVATIONAL_MESSAGES),
        "daily_goal": "Move your body for at least 20 minutes today.",
    }


# ---------------------------------------------------------------------------
# Tool: get_wellness_guidance
# ---------------------------------------------------------------------------
def get_wellness_guidance(topic: str = "general") -> Dict[str, Any]:
    """Return wellness tips for a given topic."""
    topic_key = topic.lower()
    tips = WELLNESS_TIPS.get(topic_key, WELLNESS_TIPS["general"])

    return {
        "topic": topic,
        "tips": random.sample(tips, min(2, len(tips))),
    }


# ---------------------------------------------------------------------------
# Tool: calculate_bmi
# ---------------------------------------------------------------------------
def calculate_bmi(weight_kg: float, height_m: float) -> Dict[str, Any]:
    """Calculate BMI and return category."""
    if height_m <= 0 or weight_kg <= 0:
        return {"error": "Weight and height must be positive values."}

    bmi = round(weight_kg / (height_m ** 2), 1)

    if bmi < 18.5:
        category = "Underweight"
        advice = "Consider a calorie-surplus diet and strength training to build healthy mass."
    elif bmi < 25.0:
        category = "Normal weight"
        advice = "Great work! Maintain a balanced diet and regular exercise routine."
    elif bmi < 30.0:
        category = "Overweight"
        advice = "A combination of cardio and strength training with a balanced diet can help."
    else:
        category = "Obese"
        advice = "Consult a healthcare professional for a personalised weight management plan."

    return {
        "bmi": bmi,
        "category": category,
        "advice": advice,
        "disclaimer": "BMI is a general indicator and does not account for muscle mass or body composition.",
    }


# ---------------------------------------------------------------------------
# Tool: calculate_calories (Harris-Benedict equation)
# ---------------------------------------------------------------------------
_ACTIVITY_MULTIPLIERS: Dict[str, float] = {
    "sedentary":      1.2,
    "light":          1.375,
    "moderate":       1.55,
    "active":         1.725,
    "very_active":    1.9,
}

def calculate_calories(
    weight_kg: float,
    height_m: float,
    age: int,
    activity_level: str = "moderate",
    sex: str = "male",
) -> Dict[str, Any]:
    """Estimate daily caloric needs using the Mifflin-St Jeor equation."""
    height_cm = height_m * 100
    if sex.lower() == "female":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5

    multiplier = _ACTIVITY_MULTIPLIERS.get(activity_level.lower(), 1.55)
    tdee = round(bmr * multiplier)

    return {
        "bmr": round(bmr),
        "tdee": tdee,
        "for_weight_loss":  tdee - 500,
        "for_weight_gain":  tdee + 300,
        "for_maintenance":  tdee,
        "note": "These are estimates. Consult a dietitian for a personalised plan.",
    }


# ---------------------------------------------------------------------------
# Tool registry (used by ToolGuardrail)
# ---------------------------------------------------------------------------
TOOL_REGISTRY: Dict[str, Any] = {
    "get_workout_plan":     get_workout_plan,
    "get_meal_suggestion":  get_meal_suggestion,
    "get_motivation_message": get_motivation_message,
    "get_wellness_guidance": get_wellness_guidance,
    "calculate_bmi":        calculate_bmi,
    "calculate_calories":   calculate_calories,
}
