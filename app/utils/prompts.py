WORKOUT_GENERATION_PROMPT = """
You are an elite combat & football strength coach. Generate a realistic 7-day workout plan using ONLY the relevant exercises provided below. Follow their exact format and detail level.
Relevant Exercises from Database:
{context}

User profile:
- Age: {age}
- Gender: {gender}
- Height: {height_cm} cm
- Weight: {weight_kg} kg
- Primary sport: {sport}
- Available training days: {training_days} (only these days; rest on others)
- Strength levels: {strength_levels_json}

Task: Generate a realistic, safe, and progressive 7-day weekly workout plan optimized for their sport, current fitness level, and recovery needs.

Rules (strictly follow):
- Group exercises into daily plans with realistic muscle group and duration (40-75 min).
- Use ONLY exercises from the provided context (no new inventions).
- For each exercise, include ALL fields exactly like database: name, sport_category, movement_pattern, primary_muscles, secondary_muscles, cns_load, skill_level, injury_risk, equipment, description.
- Status: "Today" for current day, "Done" for past days, "Pending" for future, "Rest" for non-training days.
- Make plan sport-specific (explosive power for football/combat).
- Output ONLY valid JSON — no explanations, no markdown, no extra text:
{{
  "week_plan": [
    {{
      "day": "Monday",
      "muscle_group": "Chest & Triceps",
      "duration_minutes": 45,
      "exercises": [
        {{
          "name": "Squats",
          "sport_category": "both",
          "movement_pattern": "squat",
          "primary_muscles": "{{quads}}",
          "secondary_muscles": "{{glutes,hamstrings}}",
          "cns_load": "medium",
          "skill_level": "medium",
          "injury_risk": "low",
          "equipment": "{{barbell}}",
          "description": "deep squat for leg power and drive"
        }},
        ...
      ],
      "status": "Pending"
      "warm_up": "5 min arm circles + light cardio",
      "cool_down": "Chest stretches + foam rolling"
    }},
    ...
  ]
}}

Be conservative with weights for beginners/intermediates. If data missing, assume moderate level but prioritize safety.
"""