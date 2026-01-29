from sqlalchemy.orm import Session
from ..models.recovery_model import Recovery
from datetime import datetime


def update_recovery(
    db: Session,
    user_id: int,
    muscle_group: str,
    status: str,
    tip: str
) -> Recovery:
    recovery = db.query(Recovery).filter(
        Recovery.user_id == user_id,
        Recovery.muscle_group == muscle_group
    ).first()

    if recovery:
        recovery.status = status
        recovery.tip = tip
        recovery.last_updated = datetime.utcnow()
    else:
        recovery = Recovery(
            user_id=user_id,
            muscle_group=muscle_group,
            status=status,
            tip=tip,
            last_updated=datetime.utcnow()
        )
        db.add(recovery)

    db.commit()
    db.refresh(recovery)
    return recovery