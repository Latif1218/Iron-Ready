from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CreateSubscriptionRequest(BaseModel):
    plan_type: str = Field(..., pattern="^(monthly|yearly)$")
    payment_method_id: Optional[str] = None  


class SubscriptionResponse(BaseModel):
    id: str
    status: str
    plan_type: str
    trial_end: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False

    class Config:
        from_attributes = True