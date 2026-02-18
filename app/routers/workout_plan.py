from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from sqlalchemy.orm import Session
from typing import List, Annotated

from app import schemas
from app.models.session_model import WorkoutSession
from app.models.session_model import WorkoutSession
from ..crud.notification_crud import create_notification
from ..models.workout_model import WorkoutPlan
from ..schemas.notification_schema import NotificationCreate
from ..schemas.session_schema import SessionCreate, SessionOut, SetLogCreate, SetLogOut
from ..schemas.training_schema import TrainingPlanDay, TrainingPlanResponse
from ..database import get_db
from ..authentication.user_auth import get_current_user
from ..models.user_model import User
from ..schemas.workout_schema import WorkoutPlanOut, WorkoutGenerateRequest
from ..services.workout_service import generate_workout_plan_service
from ..services.recovery_tip_service import generate_recovery_tip
from ..crud import workout_crud, session_crud, recovery_crud, notification_crud
from ..utils import recovery
from ..config import groq_client
import logging


router = APIRouter(
    prefix="/workouts",
    tags=["Workouts"]
)

logger = logging.getLogger(__name__)

@router.post(
    "/generate",
    status_code=status.HTTP_201_CREATED,
    response_model=List[WorkoutPlanOut]
)
def generate_workout_plan(
    request: Annotated[WorkoutGenerateRequest | None, Body(embed=True, description="No body required (empty {} acceptable)")] = None,
    current_user: Session = Depends(get_current_user),
    db: Session = Depends(get_db)
):  
    """
    - Requires user to be onboarded.
    - Uses Groq API + RAG (Chroma DB with exercises.xlsx).
    - Body is optional — send {} or nothing.
    """
   
    if not current_user.onboarding or not current_user.onboarding.is_onboarded:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must complete onboarding first."
        )

    try:
        created_plans = generate_workout_plan_service(current_user, db)
        
        create_notification(
            db,
            NotificationCreate(message="New workout plan generated! Check your plan now."),
            current_user.id
        )

        return created_plans

    except ValueError as ve:
        logger.warning(f"Validation error for user {current_user.id}: {str(ve)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

    except RuntimeError as re:
        logger.error(f"Runtime error during plan generation for user {current_user.id}: {str(re)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(re))

    except Exception as e:
        logger.exception(f"Unexpected error during plan generation for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during plan generation: {str(e)}"
        )
    

# get all workouts for current user
@router.get(
    "/", 
    response_model=List[WorkoutPlanOut],
    status_code=status.HTTP_200_OK
)
def get_workouts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    plans = workout_crud.get_workout_plans(db, current_user.id)
    
    if not plans:
        return []
    return plans




@router.get("/plan", response_model=TrainingPlanResponse)
def get_training_plan(
    view: Annotated[str, Query(pattern="^(today|weekly)$")] = "today",
    db: Session = Depends(get_db),
    current_user: Session = Depends(get_current_user)
):
    today = datetime.utcnow().strftime("%A")

    query = db.query(WorkoutPlan).filter(
        WorkoutPlan.user_id == current_user.id,
        WorkoutPlan.week == 1
    )

    if view == "today":
        query = query.filter(WorkoutPlan.day == today)

    plans = query.order_by(WorkoutPlan.day).all()

    if not plans:
        return TrainingPlanResponse(
            view=view,
            today=today,
            get_ready_message="No plan for today. Generate one!",
            plans=[]
        )

    response_plans = []
    for plan in plans:
        status = "Rest"
        if plan.day == today:
            status = "Today"
        elif plan.generated_at.date() < datetime.utcnow().date():
            status = "Done"

        exercises_list = plan.exercises
        if exercises_list and isinstance(exercises_list[0], dict):
            exercises_list = [ex.get("name", "Unknown") for ex in exercises_list]

        response_plans.append(TrainingPlanDay(
            day=plan.day,
            muscle_group=plan.muscle_group,
            duration=plan.duration,
            exercises=exercises_list,
            warm_up=plan.warm_up,
            cool_down=plan.cool_down,
            status=status,
            workout_id=plan.id
        ))

    get_ready = "Get ready with warm-up!" if any(p.status == "Today" for p in response_plans) else "Rest day today"

    return TrainingPlanResponse(
        view=view,
        today=today,
        get_ready_message=get_ready,
        plans=response_plans
    )




@router.post(
    "/sessions",
    response_model=SessionOut,
    status_code=status.HTTP_201_CREATED
)
def start_session(
    session: SessionCreate,
    db: Session = Depends(get_db),
    current_user:Session = Depends(get_current_user)
):
    workout = db.query(WorkoutPlan).filter(
        WorkoutPlan.id == session.workout_id,
        WorkoutPlan.user_id == current_user.id
    ).first()

    if not workout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout plan not found or does not belong to you."
        )

    return session_crud.create_session(db, session, current_user.id)


@router.put(
    "/sessions/{session_id}/complete",
    response_model=SessionOut,
    status_code=status.HTTP_200_OK
)
def complete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user:Session = Depends(get_current_user)
):
    session = session_crud.update_session_end(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session not found or already completed."
        )

    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to complete this session."
        )

    workout = db.query(WorkoutPlan).filter(
        WorkoutPlan.id == session.workout_id
    ).first()
    if not workout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated workout plan not found."
        )

    muscle_groups = [m.strip() for m in workout.muscle_group.split(",") if m.strip()]

    for muscle in muscle_groups:
        recovery_status, base_tip = recovery_crud.calculate_recovery(session.end_time)  # ← recovery_status নাম change

        try:
            prompt = f"Give a short recovery tip for {muscle} muscle group after intense workout. Max 50 words. Make it actionable."
            response = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                max_tokens=100
            )
            llm_tip = response.choices[0].message.content.strip()
        except Exception:
            llm_tip = base_tip
        recovery_crud.update_recovery(db, current_user.id, muscle, recovery_status, llm_tip)
    notification_crud.create_notification(
        db,
        NotificationCreate(
            message="Great job! Session completed. Check your recovery status and plan your next workout."
        ),
        current_user.id
    )

    return session

@router.post(
    "/sessions/{session_id}/logs",
    response_model=SetLogOut,
    status_code=status.HTTP_201_CREATED,

)
def log_set(
    session_id: int,
    log: SetLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(WorkoutSession).filter(  
        WorkoutSession.id == session_id,
        WorkoutSession.user_id == current_user.id,
        WorkoutSession.completed == False
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found, not yours, or already completed."
        )

    return session_crud.create_set_log(db, log, session_id)




@router.get("/body_diagram", response_model=)
def get_body_diagram(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    recoveries = recovery_crud.get_user_recoveries(db, current_user.id)
    front = {}
    back = {}
    tips = {}

    # Assume mapping: e.g., Chest -> front, Back -> back (hardcode or from MuscleGroup)
    for rec in recoveries:
        # Example mapping
        if rec.muscle_group in ["Chest", "Quads", "Abs"]:
            front[rec.muscle_group] = rec.status
        else:
            back[rec.muscle_group] = rec.status
        tips[rec.muscle_group] = rec.tip

    return BodyDiagramResponse(front=front, back=back, tips=tips)