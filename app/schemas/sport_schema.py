from pydantic import BaseModel, Field
from typing import List, Optional

class SportCreate(BaseModel):
    name: str = Field(..., unique=True)
    category: str
    sub_category: Optional[str]
    exercises: List[int]  # Exercise IDs to assign

class SportOut(SportCreate):
    id: int

    class Config:
        from_attributes = True