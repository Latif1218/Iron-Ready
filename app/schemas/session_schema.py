from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class SessionCreate(BaseModel):
    workout_id: int = Field(..., description="ID of the workout plan to start session for")


class SessionOut(BaseModel):
    id: int
    user_id: int
    workout_id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    completed: bool

    class Config:
        from_attributes = True


class SetLogCreate(BaseModel):
    exercise_name: str = Field(..., description="Name of the exercise (e.g., 'Bench Press')")
    set_number: int = Field(..., ge=1, description="Set number (1, 2, 3...)")
    reps_done: int = Field(..., ge=0, description="Reps completed in this set")
    weight_used: Optional[float] = Field(None, description="Weight used in kg/lbs")
    notes: Optional[str] = None


class SetLogOut(BaseModel):
    id: int
    session_id: int
    exercise_name: str
    set_number: int
    reps_done: int
    weight_used: Optional[float]
    notes: Optional[str]

    class Config:
        from_attributes = True