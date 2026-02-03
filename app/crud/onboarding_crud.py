from sqlalchemy.orm import Session
from ..models.onboarding_model import Onboarding


def get_onboarding(db: Session, user_id: int) -> Onboarding | None:
    return db.query(Onboarding).filter(Onboarding.user_id == user_id).first()


def get_or_create_onboarding(db: Session, user_id: int) -> Onboarding:
    onboarding = get_onboarding(db, user_id)
    if not onboarding:
        onboarding = Onboarding(user_id=user_id)
        db.add(onboarding)
        db.commit()
        db.refresh(onboarding)
    return onboarding