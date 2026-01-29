from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import List
from app.crud.notification_crud import create_notification
from app.models.workout_model import WorkoutPlan
from app.schemas.notification_schema import NotificationCreate
from app.schemas.session_schema import SessionCreate, SessionOut, SetLogCreate, SetLogOut
from ..database import get_db
from ..authentication.user_auth import get_current_user
from ..models.user_model import User
from ..schemas.workout_schema import WorkoutPlanOut, WorkoutGenerateRequest
from ..services.workout_service import generate_workout_plan_service
from ..services.recovery_tip_service import generate_recovery_tip
from ..crud import workout_crud, session_crud, recovery_crud
from ..utils import recovery


router = APIRouter(
    prefix="/workouts",
    tags=["Workouts"]
)


@router.post(
    "/generate",
    status_code=status.HTTP_201_CREATED,
    response_model=List[WorkoutPlanOut]
)
def generate_workout_plan(
    request: WorkoutGenerateRequest,  
    current_user:Session = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        plans = generate_workout_plan_service(current_user, db)
        return plans
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unexpected error: {str(ve)}")
    except RuntimeError as re:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error: {str(re)}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error: {str(e)}")
    
    
    
    

@router.get(
    "/", 
    response_model=List[WorkoutPlanOut],
    status_code=status.HTTP_200_OK
)
def get_workouts(
    db: Session = Depends(get_db),
    current_user:Session = Depends(get_current_user)
):
    plans = workout_crud.get_workout_plans(db, current_user.id)
    
    if not plans:
        return []
    return plans



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
        status, base_tip = recovery.calculate_recovery(session.end_time)  

        llm_tips = generate_recovery_tip(
            muscle_group=muscle,
            intensity="intense",
            max_words=50
        )
        
        recovery_crud.update_recovery(
            db, current_user.id, muscle, status, llm_tips
        )
        
    create_notification(
        db,
        NotificationCreate(
            message="Great job! Workout session completed. Check your recovery status and plan your next session."
        ),
        current_user.id
    )

    return session
        


@router.post(
    "/sessions/{session_id}/logs",
    response_model=SetLogOut,
    status_code=status.HTTP_201_CREATED,
    summary="Log a set in active session",
    description="Records reps/weight for an exercise set. Session must be active and belong to user."
)
def log_set(
    session_id: int,
    log: SetLogCreate,
    db: Session = Depends(get_db),
    current_user:Session = Depends(get_current_user)
):
    session = db.query(Session).filter(
        Session.id == session_id,
        Session.user_id == current_user.id,
        Session.completed == False
    ).first()

    if not session:
        raise HTTPException(
            status_code=400,
            detail="Session not found, not yours, or already completed."
        )

    return session_crud.create_set_log(db, log, session_id)