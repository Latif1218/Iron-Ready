from sqlalchemy import Column, Integer, String, Text, Enum
from sqlalchemy.orm import relationship
from ..database import Base
from enum import Enum as PyEnum

class CNSEnum(PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class SkillEnum(PyEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class InjuryRiskEnum(PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    category = Column(String, nullable=False)
    primary_muscle = Column(String, nullable=False)
    secondary_muscle = Column(String, nullable=True)

    cns_load = Column(Enum(CNSEnum), nullable=False)
    skill_level = Column(Enum(SkillEnum), nullable=False)
    injury_risk = Column(Enum(InjuryRiskEnum), nullable=False)

    equipment = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)

    sports = relationship("SportExercise", back_populates="exercise")
    recoveries = relationship("ExerciseRecovery", back_populates="exercise")
