from sqlalchemy import Column, Integer, String
from ..database import Base

class OnboardingContent(Base):
    __tablename__ = "onboarding_contents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    subtitle = Column(String, nullable=False)
    image_url = Column(String, nullable=False)
    order = Column(Integer, nullable=False, unique=True)