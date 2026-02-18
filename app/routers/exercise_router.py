from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List, Annotated
from ..database import get_db
from ..models.exercise_model import Exercise
from ..schemas.exercise_schema import ExerciseCreate, ExerciseOut
from ..authentication.user_auth import get_current_admin_user
from ..models.user_model import User
import shutil
import os

router = APIRouter(
    prefix="/exercises",
    tags=["Exercises"]
)

UPLOAD_DIR = "uploads/exercises"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/", response_model=ExerciseOut)
def create_exercise(
    exercise: ExerciseCreate,
    image: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    if db.query(Exercise).filter(Exercise.name == exercise.name).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Exercise name already exists"
        )
    new_ex = Exercise(**exercise.dict(exclude_unset=True))

    if image:
        file_Path = os.path.join(UPLOAD_DIR, image.filename)
        with open(file_Path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        new_ex.image_url = f"/{file_Path}"

    db.add(new_ex)
    db.commit()
    db.refresh(new_ex)
    return new_ex


@router.get("/", response_model=List[ExerciseOut])
def get_exercises(db: Session = Depends(get_db)):
    return db.query(Exercise).all()


@router.put("/{ex_id}", response_model=ExerciseOut)
def update_exercise(
    ex_id: int,
    data: ExerciseCreate,
    image: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    ex = db.query(Exercise).filter(
        Exercise.id == ex_id
    ).first()
    if not ex:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found"
        )
    
    for key, value in data.dict(exclude_unset=True).items():
        setattr(ex, key, value)

    if image:
        file_path = os.path.join(UPLOAD_DIR, image.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        ex.image_url = f"/{file_path}"

    db.commit()
    db.refresh(ex)
    return ex



@router.delete("/{ex_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exercise(
    ex_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    ex = db.query(Exercise).filter(Exercise.id == ex_id).first()
    if not ex:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found"
        )
    db.delete(ex)
    db.commit()

    