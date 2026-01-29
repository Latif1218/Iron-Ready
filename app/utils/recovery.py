from datetime import datetime, timedelta
from typing import Tuple


def calculate_recovery(last_workout_time: datetime | None) -> Tuple[str, str]:
    """
    Calculate muscle recovery status and base tip based on last workout time.
    
    Returns:
        (status, base_tip)
        status: "red" (avoid), "yellow" (light work), "green" (ready)
    """
    if not last_workout_time:
        return "green", "No previous workout data. Ready to train."

    now = datetime.utcnow()
    hours_since = (now - last_workout_time).total_seconds() / 3600

    if hours_since < 24:
        status = "red"
        base_tip = "Avoid training this muscle today. Full rest recommended."
    elif hours_since < 48:
        status = "yellow"
        base_tip = "Light mobility or active recovery recommended. Avoid heavy load."
    else:
        status = "green"
        base_tip = "Fully recovered. Safe to train with normal or increased intensity."

    return status, base_tip