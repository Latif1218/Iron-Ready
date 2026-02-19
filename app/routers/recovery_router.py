from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Annotated, Optional
from fastapi_pagination import Page, Params, paginate
from ..database import get_db
from ..models.exercise_recovery_model import ExerciseRecovery
from ..models.exercise_model import Exercise 
from ..schemas.exercise_recovery_schema import ExerciseRecoveryCreate, ExerciseRecoveryOut
from ..authentication.user_auth import get_current_admin_user
from ..models.user_model import User



router = APIRouter(
    prefix="/recovery",
    tags=["Recovery (Admin)"]
)


@router.post("/", response_model=ExerciseRecoveryOut, status_code=status.HTTP_201_CREATED)
def assign_recovery(
    data: ExerciseRecoveryCreate,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[User, Depends(get_current_admin_user)]
):
    existing = db.query(ExerciseRecovery).filter(
        ExerciseRecovery.exercise_id == data.exercise_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recovery details already assigned for this exercise"
        )
    
    if not db.query(Exercise).filter(Exercise.id == data.exercise_id).first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found"
        )
    new_recovery = ExerciseRecovery(**data.model_dump())
    db.add(new_recovery)
    db.commit()
    db.refresh(new_recovery)
    return new_recovery