from pydantic import BaseModel, Field
from typing import List, Optional


class SportCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Name of the sport (must be unique)",
        examples=["Boxing", "Judo", "Wrestling"]
    )
    category: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Main category of the sport",
        examples=["Combat", "Football", "Gymnastics"]
    )
    sub_category: Optional[str] = Field(
        None,
        max_length=50,
        description="Optional sub-category",
        examples=["Boxing", "Judo", "Freestyle"]
    )
    exercise_ids: List[int] = Field(
        default_factory=list,
        description="List of existing exercise IDs to assign to this sport (max 10)",
        max_items=10,  
        examples=[[1, 5, 8], [3, 7, 12, 15]]
    )


class SportOut(SportCreate):
    id: int = Field(..., description="Auto-generated unique ID of the sport")

    class Config:
        from_attributes = True  
        json_encoders = {
            
        }