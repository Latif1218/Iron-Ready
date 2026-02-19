from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class Sport(Base):
    __tablename__ = "sports"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    category = Column(String, nullable=False)
    sub_category = Column(String, nullable=True)

    exercises = relationship(
        "Exercise",
        secondary="sport_exercises",
        back_populates="sports"
    )

sport_exercises = Table(
    "sport_exercises",
    Base.metadata,
    Column("sport_id", Integer, ForeignKey("sports.id"), primary_key=True),
    Column("exercise_id", Integer, ForeignKey("exercises.id"), primary_key=True)
)