from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Annotated
from ..database import get_db
from ..models.exercise_model import Exercise
from ..models.sport_model import Sport, sport_exercises
from ..schemas.sport_schema import SportCreate, SportOut
from ..authentication.user_auth import get_current_admin_user
from ..models.user_model import User


router = APIRouter(
    prefix="/sports",
    tags=["Sports"]
)

@router.post(
    "/",
    response_model=SportOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create new sport and assign exercises (Admin only)"
)
def create_sport(
    sport: SportCreate,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[User, Depends(get_current_admin_user)]
):
    if db.query(Sport).filter(Sport.name.ilike(sport.name)).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sport name already exists"
        )

    new_sport = Sport(
        name=sport.name.strip(),
        category=sport.category.strip(),
        sub_category=sport.sub_category.strip() if sport.sub_category else None
    )
    db.add(new_sport)
    db.flush()  

    if sport.exercise_ids:
        if len(sport.exercise_ids) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 10 exercises allowed per sport"
            )

        for ex_id in sport.exercise_ids:
            if not db.query(Exercise).filter(Exercise.id == ex_id).first():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Exercise with ID {ex_id} not found"
                )

            db.execute(
                sport_exercises.insert().values(
                    sport_id=new_sport.id,
                    exercise_id=ex_id
                )
            )

    db.commit()
    db.refresh(new_sport)

    return new_sport


@router.get("/{sport_id}", response_model=SportOut)
def get_sport(
    sport_id: int,
    db: Annotated[Session, Depends(get_db)]
):
    sport = db.query(Sport).filter(Sport.id == sport_id).first()
    if not sport:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sport not found"
        )
    return sport