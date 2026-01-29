from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import json
from openai import OpenAI
import os

from ..models.user_model import User
from ..models.workout_model import WorkoutPlan
from ..schemas.workout_schema import WorkoutPlanOut
from ..utils.prompts import WORKOUT_GENERATION_PROMPT

groq_client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)


def generate_workout_plan_service(
    current_user: User,
    db: Session
) -> List[WorkoutPlanOut]:
    """
    Core function to generate and save workout plan using Groq API.
    Returns list of created WorkoutPlanOut objects.
    """
    if not current_user.is_onboarded:
        raise ValueError("User must complete onboarding first.")

   
    age = current_user.age or 25
    gender = current_user.gender or "not specified"
    height_cm = current_user.height or 170.0
    weight_kg = current_user.weight or 70.0
    sport = current_user.sport or "general fitness"
    training_days = current_user.training_days or ["Monday", "Wednesday", "Friday"]
    strength_levels = current_user.strength_levels or {}

   
    formatted_prompt = WORKOUT_GENERATION_PROMPT.format(
        age=age,
        gender=gender,
        height_cm=height_cm,
        weight_kg=weight_kg,
        sport=sport,
        training_days=", ".join(training_days),
        strength_levels_json=json.dumps(strength_levels, ensure_ascii=False)
    )

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are an expert fitness coach. Output ONLY valid JSON. No extra text."},
                {"role": "user", "content": formatted_prompt}
            ],
            temperature=0.35,
            max_tokens=2500,
            response_format={"type": "json_object"}
        )

        raw_output = response.choices[0].message.content.strip()

        plan_data = json.loads(raw_output)
        week_plan = plan_data.get("week_plan", [])

        if not week_plan or not isinstance(week_plan, list):
            raise ValueError("No valid week_plan in Groq response")

        created_plans = []
        for day_plan in week_plan:
            if not {"day", "muscle_group", "duration_minutes", "exercises"}.issubset(day_plan.keys()):
                continue

            db_plan = WorkoutPlan(
                user_id=current_user.id,
                week=1,
                day=day_plan["day"],
                muscle_group=day_plan["muscle_group"],
                duration=day_plan["duration_minutes"],
                exercises=day_plan["exercises"],
                warm_up=day_plan.get("warm_up", ""),
                cool_down=day_plan.get("cool_down", ""),
                generated_at=datetime.utcnow()
            )
            db.add(db_plan)
            created_plans.append(db_plan)

        db.commit()
        for plan in created_plans:
            db.refresh(plan)

        return [WorkoutPlanOut.from_orm(p) for p in created_plans]

    except json.JSONDecodeError as parse_err:
        raise ValueError(f"Failed to parse Groq response: {str(parse_err)}")
    except Exception as e:
        db.rollback()
        raise RuntimeError(f"Groq API or processing error: {str(e)}")
    
    
