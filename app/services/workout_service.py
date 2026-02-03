import json
import logging
from datetime import datetime, timedelta
from typing import List

from sqlalchemy.orm import Session
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from ..models.user_model import User
from ..models.workout_model import WorkoutPlan
from ..schemas.workout_schema import WorkoutPlanOut
from ..utils.prompts import WORKOUT_GENERATION_PROMPT
from ..config import groq_client

logger = logging.getLogger(__name__)

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = Chroma(
    collection_name="iron_ready_exercises",
    embedding_function=embeddings,
    persist_directory="./chroma_db_exercise"
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 10})


def generate_workout_plan_service(
    current_user: User,
    db: Session
) -> List[WorkoutPlanOut]:
    """
    Generate and save personalized 7-day workout plan with full exercise details.
    """
    if not current_user.onboarding or not current_user.onboarding.is_onboarded:
        raise ValueError("User must complete onboarding first.")

    onboarding = current_user.onboarding

    age = onboarding.age or 25
    gender = onboarding.gender or "not specified"
    height_cm = onboarding.height_cm or 170.0
    weight_kg = onboarding.weight_kg or 70.0
    
    sport_category = onboarding.sport_category or "general fitness"
    sport_sub_category = onboarding.sport_sub_category or None
    sport = sport_category
    if sport_sub_category:
        sport += f" ({sport_sub_category})"

    training_days = onboarding.training_days or ["Monday", "Wednesday", "Friday"]
    strength_levels = onboarding.strength_levels or {}

    query = (
        f"Exercises for {sport} sport, training days: {', '.join(training_days)}, "
        f"patterns: press, hinge, squat, pull, jump, rotate, carry"
    )
    docs = retriever.invoke(query)
    context = "\n\n".join([doc.page_content for doc in docs])

    logger.info(f"Retrieved {len(docs)} exercises for user {current_user.id}")

    formatted_prompt = WORKOUT_GENERATION_PROMPT.format(
        age=age,
        gender=gender,
        height_cm=height_cm,
        weight_kg=weight_kg,
        sport=sport,
        training_days=", ".join(training_days),
        strength_levels_json=json.dumps(strength_levels, ensure_ascii=False),
        context=context
    )

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Output ONLY valid JSON. No explanations, no markdown, no extra text."},
                {"role": "user", "content": formatted_prompt}
            ],
            temperature=0.35,
            max_tokens=3000,
            response_format={"type": "json_object"}
        )

        raw_output = response.choices[0].message.content.strip()
        logger.debug(f"Groq raw output (first 500 chars): {raw_output[:500]}...")

        plan_data = json.loads(raw_output)
        week_plan = plan_data.get("week_plan", [])

        if not week_plan or not isinstance(week_plan, list):
            raise ValueError("No valid 'week_plan' list in response")

    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e} | Raw output: {raw_output}")
        raise ValueError("LLM output is not valid JSON")
    except Exception as e:
        logger.error(f"Groq error: {e}")
        raise RuntimeError(f"Generation failed: {e}")

    created_plans = []
    try:
        today = datetime.utcnow().date()
        weekday = today.weekday()
        week_start_date = today - timedelta(days=weekday)

        day_to_index = {
            "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
            "Friday": 4, "Saturday": 5, "Sunday": 6
        }

        for day_plan in week_plan:
            required = {"day", "muscle_group", "duration", "exercises"}
            missing = required - set(day_plan.keys())
            if missing:
                logger.warning(f"Skipping day '{day_plan.get('day')}': missing {missing}")
                continue

            day_name = day_plan["day"]
            if day_name not in day_to_index:
                logger.warning(f"Invalid day: {day_name}")
                continue

            day_offset = day_to_index[day_name]
            plan_date = week_start_date + timedelta(days=day_offset)
            plan_datetime = datetime.combine(plan_date, datetime.min.time())

            status = "Today" if plan_date == today else \
                     "Done" if plan_date < today else \
                     day_plan.get("status") or "Pending"

           
            exercises = day_plan.get("exercises", [])

            
            if not isinstance(exercises, list) or not exercises:
                exercises = [{"name": "No exercises provided"}]
            elif not all(isinstance(ex, dict) for ex in exercises):
                logger.warning("Invalid exercises format from LLM")
                exercises = [{"name": "Invalid exercise data"}]

            db_plan = WorkoutPlan(
                user_id=current_user.id,
                week=1,
                day=day_name,
                plan_datetime=plan_datetime,
                muscle_group=day_plan["muscle_group"],
                duration=day_plan.get("duration", 45),
                exercises=exercises,  
                warm_up=day_plan.get("warm_up", ""),
                cool_down=day_plan.get("cool_down", ""),
                status=status,
                generated_at=datetime.utcnow()
            )

            db.add(db_plan)
            created_plans.append(db_plan)

        if not created_plans:
            logger.warning("No valid days saved")

        db.commit()
        for plan in created_plans:
            db.refresh(plan)

        logger.info(f"Saved {len(created_plans)} plans for user {current_user.id}")

        return [WorkoutPlanOut.from_orm(p) for p in created_plans]

    except Exception as e:
        db.rollback()
        logger.error(f"DB error: {str(e)}")
        raise RuntimeError(f"Failed to save plans: {str(e)}")