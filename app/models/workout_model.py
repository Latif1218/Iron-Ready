from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base
from datetime import datetime

class WorkoutPlan(Base):
    __tablename__ = "workout_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    week = Column(Integer, default=1)
    day = Column(String, nullable=False)
    muscle_group = Column(String, nullable=False)
    duration = Column(Integer, nullable=False)  
    exercises = Column(JSON, nullable=False)    
    warm_up = Column(String, nullable=True)
    cool_down = Column(String, nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="workout_plans")