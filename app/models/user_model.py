from sqlalchemy import Column, Integer, String, Boolean, Float, Date, JSON, TIMESTAMP, text, DateTime
from sqlalchemy.orm import relationship
from ..database import Base
from cuid2 import Cuid
from datetime import datetime

cuid = Cuid()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key = True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="user") # user, admin, superadmin
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=datetime.utcnow)
    
    onboarding = relationship("Onboarding", back_populates="user", uselist=False)
    subscription = relationship("Subscription", back_populates="user", uselist=False)
    workout_plans = relationship("WorkoutPlan", back_populates="user")
    sessions = relationship("WorkoutSession", back_populates="user")
    recoveries = relationship("Recovery", back_populates="user")
    notifications = relationship("Notification", back_populates="user", order_by="Notification.created_at.desc()")