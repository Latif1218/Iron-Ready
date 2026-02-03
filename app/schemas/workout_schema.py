from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime


class WorkoutGenerateRequest(BaseModel):
    """
    Request body for generating workout plan.
    Send empty JSON object {} — no fields required.
    All data is pulled from user's onboarding profile.
    """
    pass  

class ExerciseDetail(BaseModel):
    name: str
    sport_category: Optional[str] = None
    movement_pattern: Optional[str] = None
    primary_muscles: Optional[str] = None
    secondary_muscles: Optional[str] = None
    cns_load: Optional[str] = None
    skill_level: Optional[str] = None
    injury_risk: Optional[str] = None
    equipment: Optional[str] = None
    description: Optional[str] = None


class WorkoutPlanOut(BaseModel):
    id: int
    user_id: int
    week: int
    day: str
    plan_datetime: datetime
    muscle_group: str
    duration: int
    exercises: List[ExerciseDetail]  
    warm_up: Optional[str] = None
    cool_down: Optional[str] = None
    status: str
    generated_at: datetime

    class Config:
        from_attributes = True