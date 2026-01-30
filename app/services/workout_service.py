import json
import logging
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from langchain_community.vectorstores import Chroma
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
    Generate personalized workout plan using:
    - User registration/onboarding data
    - Relevant exercises retrieved from Excel via RAG (Chroma DB)
    
    Returns: List of created WorkoutPlanOut objects
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

    query = f"Exercises for {sport} sport, training days {', '.join(training_days)}, patterns: press, hinge, squat, pull, jump, rotate, carry"
    docs = retriever.invoke(query)  

    context = "\n\n".join([doc.page_content for doc in docs])
    logger.info(f"Retrieved {len(docs)} relevant exercises for user {current_user.id}")

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
                {"role": "system", "content": "Output ONLY valid JSON. No extra text or explanations."},
                {"role": "user", "content": formatted_prompt}
            ],
            temperature=0.35,
            max_tokens=3000,
            response_format={"type": "json_object"}
        )

        raw_output = response.choices[0].message.content.strip()
        logger.debug(f"Groq raw output: {raw_output[:200]}...")

        plan_data = json.loads(raw_output)
        week_plan = plan_data.get("week_plan", [])

        if not week_plan or not isinstance(week_plan, list):
            raise ValueError("Invalid or empty 'week_plan' in Groq response")

    except json.JSONDecodeError as parse_err:
        logger.error(f"JSON parse failed: {str(parse_err)} - Raw: {raw_output}")
        raise ValueError(f"Failed to parse generated plan: {str(parse_err)}")
    except Exception as api_err:
        logger.error(f"Groq API error: {str(api_err)}")
        raise RuntimeError(f"Groq generation failed: {str(api_err)}")

  
    created_plans = []
    try:
        for day_plan in week_plan:
            required = {"day", "muscle_group", "duration", "exercises"}
            if not required.issubset(day_plan.keys()):
                logger.warning(f"Skipping invalid day plan: {day_plan.get('day', 'unknown')}")
                continue

            db_plan = WorkoutPlan(
                user_id=current_user.id,
                week=1,
                day=day_plan["day"],
                muscle_group=day_plan["muscle_group"],
                duration=day_plan.get("duration", 45), 
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

        logger.info(f"Generated & saved {len(created_plans)} workout plans for user {current_user.id}")

        return [WorkoutPlanOut.from_orm(p) for p in created_plans]

    except Exception as db_err:
        db.rollback()
        logger.error(f"Database save failed: {str(db_err)}")
        raise RuntimeError(f"Failed to save workout plans: {str(db_err)}")