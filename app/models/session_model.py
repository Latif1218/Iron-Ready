from sqlalchemy import Column, Integer, ForeignKey, DateTime, Boolean, String, Float
from sqlalchemy.orm import relationship
from ..database import Base
from datetime import datetime


class WorkoutSession(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    workout_id = Column(Integer, ForeignKey("workout_plans.id"), nullable=False, index=True)
    start_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_time = Column(DateTime, nullable=True)
    completed = Column(Boolean, default=False, nullable=False)
    notes = Column(String, nullable=True)

    user = relationship("User", back_populates="sessions")
    workout = relationship("WorkoutPlan", back_populates="sessions")
    set_logs = relationship("SetLog", back_populates="session", cascade="all, delete-orphan")

class SetLog(Base):
    __tablename__ = "set_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    exercise_name = Column(String, nullable=False) 
    set_number = Column(Integer, nullable=False)
    reps_done = Column(Integer, nullable=False)
    weight_used = Column(Float, nullable=True) 
    notes = Column(String, nullable=True)

    session = relationship("WorkoutSession", back_populates="set_logs")