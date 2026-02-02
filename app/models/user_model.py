from sqlalchemy import Column, Integer, String, Boolean, Float, Date, JSON, TIMESTAMP, text
from sqlalchemy.orm import relationship
from ..database import Base
from cuid2 import Cuid

cuid = Cuid()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key = True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    birth_date = Column(Date, nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)
    height = Column(Float, nullable=True)
    weight = Column(Float, nullable=True)
    sport = Column(String, nullable=True)
    strength_levels = Column(JSON, nullable=True)  # {"bench": 135, "squat": 200, "jump": 20}
    training_days = Column(JSON, nullable=True)  # ["Mon", "Wed", "Fri"]
    is_onboarded = Column(Boolean, default=False, nullable=False)
    onboarding_completed_at = Column(TIMESTAMP(timezone=True), nullable=True, server_default=text('now()'))
    is_active = Column(Boolean, default=True)
    role = Column(String, default="user") # user, admin, superadmin
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    
    
    subscription = relationship("Subscription", back_populates="user", uselist=False)
    workout_plans = relationship("WorkoutPlan", back_populates="user")
    sessions = relationship("WorkoutSession", back_populates="user")
    recoveries = relationship("Recovery", back_populates="user")
    notifications = relationship("Notification", back_populates="user", order_by="Notification.created_at.desc()")