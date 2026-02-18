from pydantic import BaseModel, Field

class OnboardingContentUpdate(BaseModel):
    title: str
    subtitle: str
    image_url: str
    order: int

class OnboardingContentOut(OnboardingContentUpdate):
    id: int

    class Config:
        from_attributes = True