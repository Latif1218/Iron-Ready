from sqlalchemy.orm import Session
from ..models.recovery_model import Recovery
from datetime import datetime
from typing import List, Tuple


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




def get_user_recoveries(db: Session, user_id: int) -> List[Recovery]:
    return db.query(Recovery).filter(Recovery.user_id == user_id).all()


def calculate_recovery(last_workout_end_time: datetime | None) -> Tuple[str, str]:
    """
    Calculate muscle recovery status and a basic recovery tip based on last workout end time.

    Args:
        last_workout_end_time (datetime | None): Session end time of the last workout for this muscle.

    Returns:
        Tuple[str, str]: (status, base_tip)
            - status: "red" (avoid heavy training), "yellow" (light work), "green" (fully recovered)
            - base_tip: Simple text tip (LLM দিয়ে enhance করা যাবে পরে)
    """
    if last_workout_end_time is None:
        return "green", "No previous workout recorded for this muscle. Ready to train!"

    now = datetime.utcnow()
    hours_since = (now - last_workout_end_time).total_seconds() / 3600

    if hours_since < 24:  
        status = "red"
        base_tip = "Avoid heavy training today. Full rest or active recovery recommended."
    elif hours_since < 48:  
        status = "yellow"
        base_tip = "Light mobility, stretching, or low-intensity work is okay. Avoid max effort."
    elif hours_since < 72: 
        status = "green"
        base_tip = "Mostly recovered. Normal training is safe, but listen to your body."
    else: 
        status = "green"
        base_tip = "Fully recovered. Safe for heavy or high-intensity training."

    return status, base_tip