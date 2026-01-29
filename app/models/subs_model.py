from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base
from enum import Enum as PyEnum


class SubscriptionStatus(str, PyEnum):
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String, primary_key=True)  
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    stripe_customer_id = Column(String, nullable=False, index=True)
    price_id = Column(String, nullable=False) 
    status = Column(Enum(SubscriptionStatus), nullable=False)
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    trial_start = Column(DateTime, nullable=True)
    trial_end = Column(DateTime, nullable=True)
    cancel_at_period_end = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="subscription")