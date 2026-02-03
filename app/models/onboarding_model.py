from sqlalchemy import Column, Integer, String, Float, Date, JSON, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from ..database import Base
from datetime import datetime


class Onboarding(Base):
    __tablename__ = "onboarding"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    birth_date = Column(Date, nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)  
    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    sport_category = Column(String, nullable=True)      
    sport_sub_category = Column(String, nullable=True)   
    strength_levels = Column(JSON, nullable=True)        
    training_days = Column(JSON, nullable=True)          
    is_onboarded = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="onboarding")