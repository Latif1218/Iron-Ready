from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime



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