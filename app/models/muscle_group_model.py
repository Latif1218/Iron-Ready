from sqlalchemy import Column, Integer, String
from ..database import Base

class MuscleGroup(Base):
    __tablename__ = "muscle_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)  # e.g., Chest, Back
    description = Column(String, nullable=True)