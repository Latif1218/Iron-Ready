from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class TrainingPlanDay(BaseModel):
    day: str = Field(..., description="Day of the week (e.g. 'Monday')")
    muscle_group: str = Field(..., description="Primary muscle focus (e.g. 'Full Body', 'Lower Body')")
    duration: int = Field(..., ge=0, description="Duration in minutes")
    exercises: List[str] = Field(..., description="List of exercise names")
    warm_up: Optional[str] = Field(None, description="Warm-up instructions")
    cool_down: Optional[str] = Field(None, description="Cool-down instructions")
    status: str = Field(..., description="Status: 'Today', 'Done', 'Pending', 'Rest'")
    workout_id: int = Field(..., description="ID of the WorkoutPlan")


class TrainingPlanResponse(BaseModel):
    view: str = Field(..., pattern="^(today|weekly)$", description="Current view mode")
    today: str = Field(..., description="Current day name (e.g. 'Monday')")
    get_ready_message: str = Field(..., description="Motivational message for user")
    plans: List[TrainingPlanDay] = Field(..., description="List of days with workout details")


class SetLogCreate(BaseModel):
    exercise_name: str = Field(..., min_length=1, description="Name of the exercise")
    set_number: int = Field(..., ge=1, description="Set number (1, 2, 3...)")
    reps_done: int = Field(..., ge=0, description="Actual reps completed")
    weight_used: Optional[float] = Field(None, ge=0, description="Weight used in kg/lbs (null for bodyweight)")
    notes: Optional[str] = Field(None, description="Optional notes or form feedback")


class SetLogOut(SetLogCreate):
    id: int = Field(..., description="Database ID of the set log")
    session_id: int = Field(..., description="ID of the parent session")

    class Config:
        from_attributes = True


class SessionOut(BaseModel):
    id: int = Field(..., description="Session ID")
    workout_id: int = Field(..., description="Linked workout plan ID")
    start_time: datetime = Field(..., description="When session started")
    end_time: Optional[datetime] = Field(None, description="When session ended (null if active)")
    completed: bool = Field(..., description="Is session finished?")

    class Config:
        from_attributes = True