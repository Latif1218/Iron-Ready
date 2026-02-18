from sqlalchemy import Column, Integer, String, table, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class Sport(Base):
    __tablename__ = "sports"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)  
    category = Column(String, nullable=False)  
    sub_category = Column(String, nullable=True)

    exercises = relationship("SportExercise", back_populates="sport")

sport_exercises = table(
    "sport_exercises",
    Column("sport_id", Integer, ForeignKey("sports.id"), primary_key=True),
    Column("exercise_id", Integer, ForeignKey("exercises.id"), primary_key=True)
)

class SportExercise(Base):
    __table__ = sport_exercises
    sport = relationship("Sport", back_populates="exercises")
    exercise = relationship("Exercise", back_populates="sports")