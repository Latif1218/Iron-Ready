from pydantic import BaseModel, Field
from typing import Optional


class OnboardingContentOut(BaseModel):
    id: int = Field(..., description="Auto-generated ID")
    title: str = Field(..., min_length=1, max_length=200)
    subtitle: str = Field(..., min_length=1, max_length=500)
    image_url: Optional[str] = Field(None, description="Relative or absolute URL of the image")

    class Config:
        from_attributes = True  