from sqlalchemy import Column, Integer, ForeignKey, String, Integer as Int
from sqlalchemy.orm import relationship
from ..database import Base

class ExerciseRecovery(Base):
    __tablename__ = "exercise_recoveries"

    id = Column(Integer, primary_key=True, index=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    cns_load_hours_low = Column(Int, default=24)
    cns_load_hours_medium = Column(Int, default=48)
    cns_load_hours_high = Column(Int, default=72)
    recovery_guidance = Column(String, nullable=True)

    exercise = relationship("Exercise", back_populates="recoveries")