from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from fastapi_pagination import Page



class RecentActivityItem(BaseModel):
    user_name: str = Field(..., description="users name")
    action: str = Field(..., description="for activation")
    time_ago: str = Field(..., description="before exact time")
    timestamp: datetime = Field(..., description="exact time")

    class Config:
        from_attributes = True




class DashboardStats(BaseModel):
    total_users: int = Field(..., ge=0)
    premium_users: int = Field(..., ge=0)
    free_users: int = Field(..., ge=0)
    total_revenue: float = Field(..., ge=0.0)
    monthly_revenue: float = Field(..., ge=0.0)
    last_month_revenue: float = Field(..., ge=0.0)
    recent_activities: List[RecentActivityItem] = Field(default_factory=list)
    updated_at: datetime = Field(...)

    class Config:
        from_attributes = True





class SubscriptionInfo(BaseModel):
    """Current subscription status (from your Subscription model)"""
    status: str = Field(..., description="e.g. active, trialing, past_due, canceled")
    current_period_end: Optional[datetime] = Field(None, description="End of current billing period")
    cancel_at_period_end: bool = Field(False, description="Will cancel at end of period?")



class OnboardingInfo(BaseModel):
    """Personal info from onboarding table"""
    age: Optional[int] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    sport_category: Optional[str] = None
    sport_sub_category: Optional[str] = None



class UserListItem(BaseModel):
    id: int = Field(..., description="User ID")
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    is_active: bool = Field(..., description="Account active status")
    role: str = Field(..., description="user / admin / superadmin")
    created_at: datetime = Field(..., description="Registration date")
    
    onboarding: Optional[OnboardingInfo] = None
    subscription: Optional[SubscriptionInfo] = None

    class Config:
        from_attributes = True  


class UserPage(Page[UserListItem]):
    """Paginated response of users"""
    pass
