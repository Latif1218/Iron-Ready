from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import Annotated, List
from datetime import datetime
import json
from openai import OpenAI
import os
from ..config import GROQ_API_KEY
from ..database import get_db
from ..authentication.user_auth import get_current_user
from ..models.user_model import User
from ..models.workout_model import WorkoutPlan
from ..schemas.workout_schema import WorkoutPlanOut, WorkoutGenerateRequest
from ..utils.prompts import WORKOUT_GENERATION_PROMPT

router = APIRouter(
    prefix="/workouts",
    tags=["Workouts"]
)

# Groq client (OpenAI-compatible)
groq_client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)


@router.post(
    "/generate",
    status_code=status.HTTP_201_CREATED,
    response_model=List[WorkoutPlanOut],
    summary="Generate weekly workout plan using Groq API",
    description=(
        "Generates personalized 7-day workout plan using fast Groq inference (Llama 3.1). "
        "Request body is REQUIRED — send empty JSON {}. "
        "All user data comes from onboarding profile (no need to send in body)."
    )
)
def generate_workout_plan(
    request: WorkoutGenerateRequest,  # mandatory body (খালি {} পাঠাতে হবে)
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    if not current_user.is_onboarded:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complete onboarding first."
        )

    # User data from DB (onboarding)
    age = current_user.age or 25
    gender = current_user.gender or "not specified"
    height_cm = current_user.height or 170.0
    weight_kg = current_user.weight or 70.0
    sport = current_user.sport or "general fitness"
    training_days = current_user.training_days or ["Monday", "Wednesday", "Friday"]
    strength_levels = current_user.strength_levels or {}

    # Prompt
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
        # Groq API call (খুব দ্রুত!)
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",  # best quality & fast (Groq-এ available)
            # অথবা "llama-3.1-8b-instant" for super speed
            messages=[
                {"role": "system", "content": "You are an expert fitness coach. Output ONLY valid JSON. No extra text."},
                {"role": "user", "content": formatted_prompt}
            ],
            temperature=0.35,           # consistent output
            max_tokens=2500,
            response_format={"type": "json_object"}
        )

        raw_output = response.choices[0].message.content.strip()

        # JSON parse
        try:
            plan_data = json.loads(raw_output)
            week_plan = plan_data.get("week_plan", [])
            if not week_plan or not isinstance(week_plan, list):
                raise ValueError("No valid week_plan in response")
        except (json.JSONDecodeError, ValueError) as e:
            raise HTTPException(500, f"Failed to parse Groq response: {str(e)}")

        # DB save
        created_plans = []
        try:
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

        except Exception as db_err:
            db.rollback()
            raise HTTPException(500, f"DB save failed: {str(db_err)}")

        return [WorkoutPlanOut.from_orm(p) for p in created_plans]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Groq API error: {str(e)}. Check GROQ_API_KEY or rate limit."
        )