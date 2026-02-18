from pydantic import BaseModel, Field
from typing import Optional
class ExerciseRecoveryCreate(BaseModel):
    exercise_id: int
    cns_load_hours_low: int = Field(24, ge=0)
    cns_load_hours_medium: int = Field(48, ge=0)
    cns_load_hours_high: int = Field(72, ge=0)
    recovery_guidance: Optional[str]

class ExerciseRecoveryOut(ExerciseRecoveryCreate):
    id: int

    class Config:
        from_attributes = True