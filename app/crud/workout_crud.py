from sqlalchemy.orm import Session
from typing import List, Optional
from ..models.workout_model import WorkoutPlan


def get_workout_plans(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    week: Optional[int] = None
) -> List[WorkoutPlan]:
    """
    Get all workout plans for a specific user.
    Supports optional pagination and week filter.
    """
    query = db.query(WorkoutPlan).filter(WorkoutPlan.user_id == user_id)

    if week is not None:
        query = query.filter(WorkoutPlan.week == week)

    return query.offset(skip).limit(limit).all()