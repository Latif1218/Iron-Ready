from pydantic import BaseModel, Field
from typing import Optional

class ExerciseCreate(BaseModel):
    name: str = Field(..., min_length=1)
    category: str
    primary_muscle: str
    secondary_muscle: Optional[str]
    cns_load: str = Field(..., pattern="^(low|medium|high)$")
    skill_level: str = Field(..., pattern="^(beginner|intermediate|advanced)$")
    injury_risk: str = Field(..., pattern="^(low|medium|high)$")
    equipment: Optional[str]
    description: Optional[str]
    image_url: Optional[str]

class ExerciseOut(ExerciseCreate):
    id: int

    class Config:
        from_attributes = True