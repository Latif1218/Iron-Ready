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

class WorkoutPlanOut(BaseModel):
    id: int
    user_id: int
    week: int
    day: str
    muscle_group: str
    duration: int
    exercises: List[Dict]
    warm_up: Optional[str]
    cool_down: Optional[str]
    generated_at: datetime

    class Config:
        from_attributes = True