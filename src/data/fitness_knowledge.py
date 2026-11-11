"""
src/data/fitness_knowledge.py
================================
Static fitness knowledge base used when the LLM is unavailable
or to ground responses with vetted content.
"""

from __future__ import annotations

from typing import Dict, List

# ---------------------------------------------------------------------------
# Workout plans by goal × experience level
# ---------------------------------------------------------------------------
WORKOUT_PLANS: Dict[str, Dict[str, List[str]]] = {
    "weight_loss": {
        "beginner": [
            "20-min brisk walk",
            "10 bodyweight squats × 3 sets",
            "10 push-ups (modified) × 3 sets",
            "30-sec plank × 3 sets",
            "20 jumping jacks × 3 sets",
        ],
        "intermediate": [
            "30-min jog or cycling",
            "15 squats × 4 sets",
            "15 push-ups × 4 sets",
            "40-sec plank × 4 sets",
            "20 burpees × 3 sets",
            "15 lunges per leg × 3 sets",
        ],
        "advanced": [
            "45-min HIIT session",
            "20 jump squats × 5 sets",
            "20 push-ups × 5 sets",
            "60-sec plank × 5 sets",
            "25 burpees × 4 sets",
            "20 split lunges per leg × 4 sets",
        ],
    },
    "muscle_gain": {
        "beginner": [
            "10 push-ups × 4 sets",
            "10 pull-ups (assisted) × 3 sets",
            "12 bodyweight squats × 4 sets",
            "12 dips (using chair) × 3 sets",
            "Plank hold 30 sec × 3 sets",
        ],
        "intermediate": [
            "15 diamond push-ups × 4 sets",
            "10 pull-ups × 4 sets",
            "15 Bulgarian split squats × 4 sets",
            "15 dips × 4 sets",
            "20 pike push-ups × 3 sets",
        ],
        "advanced": [
            "Handstand push-up progression × 5 sets",
            "15 one-arm push-up progression × 4 sets",
            "20 pistol squat progression × 4 sets",
            "15 muscle-up progression × 3 sets",
            "Dragon flag progression × 4 sets",
        ],
    },
    "general_fitness": {
        "beginner": [
            "10-min warm-up walk",
            "10 squats × 3 sets",
            "10 push-ups × 3 sets",
            "10 glute bridges × 3 sets",
            "20-sec plank × 3 sets",
            "5-min cool-down stretch",
        ],
        "intermediate": [
            "10-min warm-up jog",
            "15 squats × 4 sets",
            "15 push-ups × 4 sets",
            "15 glute bridges × 4 sets",
            "40-sec plank × 4 sets",
            "10-min yoga cool-down",
        ],
        "advanced": [
            "15-min warm-up run",
            "20 jump squats × 4 sets",
            "20 push-ups × 5 sets",
            "20 single-leg glute bridges × 4 sets",
            "60-sec plank × 5 sets",
            "10-min stretch and foam-roll",
        ],
    },
    "flexibility": {
        "beginner": [
            "Cat-cow stretch × 10 reps",
            "Child's pose 30 sec × 3 sets",
            "Hip flexor stretch 30 sec each side",
            "Seated hamstring stretch 30 sec",
            "Shoulder cross-body stretch 20 sec each arm",
        ],
        "intermediate": [
            "Sun salutation × 5 rounds",
            "Pigeon pose 60 sec each side",
            "Standing forward fold 45 sec",
            "Low lunge with twist 30 sec each side",
            "Reclined spinal twist 45 sec each side",
        ],
        "advanced": [
            "Full sun salutation flow 15 min",
            "Splits progression 90 sec each side",
            "Wheel pose hold 30 sec × 3 sets",
            "King pigeon pose 60 sec each side",
            "Scorpion pose progression",
        ],
    },
}

# ---------------------------------------------------------------------------
# Meal suggestions by dietary preference
# ---------------------------------------------------------------------------
MEAL_SUGGESTIONS: Dict[str, List[Dict[str, str]]] = {
    "balanced": [
        {"name": "Grilled chicken with quinoa and roasted vegetables",
         "calories": "~480 kcal", "protein": "~42 g"},
        {"name": "Oatmeal with banana, berries, and a boiled egg",
         "calories": "~380 kcal", "protein": "~18 g"},
        {"name": "Salmon with sweet potato and steamed broccoli",
         "calories": "~520 kcal", "protein": "~38 g"},
        {"name": "Greek yoghurt parfait with granola and mixed fruit",
         "calories": "~350 kcal", "protein": "~22 g"},
    ],
    "vegetarian": [
        {"name": "Lentil soup with whole-grain bread and salad",
         "calories": "~420 kcal", "protein": "~22 g"},
        {"name": "Tofu stir-fry with brown rice and vegetables",
         "calories": "~460 kcal", "protein": "~28 g"},
        {"name": "Chickpea and spinach curry with brown rice",
         "calories": "~490 kcal", "protein": "~20 g"},
        {"name": "Veggie omelette with whole-wheat toast",
         "calories": "~360 kcal", "protein": "~24 g"},
    ],
    "vegan": [
        {"name": "Buddha bowl: falafel, hummus, quinoa, roasted veg",
         "calories": "~550 kcal", "protein": "~20 g"},
        {"name": "Smoothie bowl: blended banana, almond milk, topped with seeds",
         "calories": "~320 kcal", "protein": "~10 g"},
        {"name": "Black bean tacos with avocado and salsa",
         "calories": "~480 kcal", "protein": "~18 g"},
        {"name": "Overnight oats with chia seeds and almond butter",
         "calories": "~400 kcal", "protein": "~14 g"},
    ],
    "high_protein": [
        {"name": "Grilled salmon with asparagus and cottage cheese",
         "calories": "~550 kcal", "protein": "~52 g"},
        {"name": "Chicken breast with egg whites and spinach omelette",
         "calories": "~430 kcal", "protein": "~58 g"},
        {"name": "Turkey meatballs with zucchini noodles",
         "calories": "~470 kcal", "protein": "~48 g"},
        {"name": "Tuna salad wrap with Greek yoghurt",
         "calories": "~390 kcal", "protein": "~44 g"},
    ],
}

# ---------------------------------------------------------------------------
# Motivational messages
# ---------------------------------------------------------------------------
MOTIVATIONAL_MESSAGES: List[str] = [
    "Every rep, every step, every choice brings you closer to your goal. Keep going! 💪",
    "Progress, not perfection. Consistency beats intensity every time.",
    "Your only competition is who you were yesterday. You're already winning.",
    "A 20-minute workout beats zero. Movement is medicine.",
    "Rest days are part of the plan – recovery is where growth happens.",
    "You don't have to be extreme, just consistent. Small steps create big changes.",
    "Drink your water, stretch your body, and celebrate every win – big or small.",
    "The hardest part is starting. Once you begin, momentum takes over.",
    "Your body is capable of more than your mind believes. Trust the process.",
    "Fitness is not a punishment – it's a celebration of what your body can do.",
]

# ---------------------------------------------------------------------------
# Wellness tips
# ---------------------------------------------------------------------------
WELLNESS_TIPS: Dict[str, List[str]] = {
    "sleep": [
        "Aim for 7–9 hours of quality sleep each night for optimal recovery.",
        "Keep a consistent sleep schedule – even on weekends.",
        "Avoid screens for 30 minutes before bed to improve sleep quality.",
        "A cool, dark room (16–19°C) promotes deeper sleep.",
    ],
    "hydration": [
        "Drink at least 2–3 litres of water daily; more on training days.",
        "Start your morning with a glass of water before coffee or tea.",
        "Monitor urine colour – pale yellow indicates good hydration.",
        "Electrolyte drinks are useful after intense sessions lasting 60+ minutes.",
    ],
    "stress": [
        "Practice 5–10 minutes of deep breathing or meditation daily.",
        "Short walks in nature can significantly reduce stress hormones.",
        "Journalling for 5 minutes helps process and release daily stress.",
        "Prioritise one task at a time – multitasking increases cortisol.",
    ],
    "general": [
        "Take the stairs, walk during lunch, and stand up every 30 minutes.",
        "Pair your workout with a post-exercise protein snack within 45 minutes.",
        "Warm up before exercise and cool down after – it prevents injury.",
        "Track your habits with a simple checklist to build consistency.",
    ],
}
