from pydantic import BaseModel, Field, field_validator
from datetime import date
from typing import List, Dict, Optional


class SportCategorySelect(BaseModel):
    sport_category: str = Field(..., description="Main sport category", examples=["Combat", "Football"])


class SportSubCategorySelect(BaseModel):
    sport_sub_category: str = Field(..., description="Sub-sport for Combat or else", examples=["Boxing", "Judo", "Karate", "Wrestling"])


class PersonalInfo(BaseModel):
    birth_date: date = Field(..., description="Date of birth (YYYY-MM-DD)")
    gender: str = Field(..., pattern="^(male|female|prefer_not_to_say)$")
    height_cm: float = Field(..., gt=100, lt=250)
    weight_kg: float = Field(..., gt=30, lt=200)


class StrengthLevels(BaseModel):
    bench_press_1rm: Optional[float] = Field(None, description="Bench Press 1RM in lbs or kg")
    back_squat_1rm: Optional[float] = Field(None, description="Back Squat 1RM in lbs or kg")
    deadlift_1rm: Optional[float] = Field(None, description="Deadlift 1RM in lbs or kg")
    vertical_jump_inches: Optional[float] = Field(None, description="Vertical Jump height in inches (from onboarding)")
    overhead_press_1rm: Optional[float] = Field(None, description="Overhead Press 1RM in lbs or kg (optional)")
    pull_up_reps: Optional[int] = Field(None, description="Max pull-ups in one set")
    push_up_reps: Optional[int] = Field(None, description="Max push-ups in one set")
    
    class Config:
        json_schema_extra = {
            "example": {
                "bench_press_1rm": 155.0,
                "back_squat_1rm": 225.0,
                "deadlift_1rm": 275.0,
                "vertical_jump_inches": 24.5,
                "overhead_press_1rm": 135.0,
                "pull_up_reps": 10,
                "push_up_reps": 25
            }
        }
    
    
class OnboardingCompleteData(BaseModel):
    strength_levels: Dict[str, float] = Field(...)
    training_days: List[str] = Field(...)

    @field_validator('training_days')
    def validate_days(cls, v):
        valid_days = {"monthly","weekly","Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}
        if not all(day in valid_days for day in v):
            raise ValueError("Invalid training days")
        return v