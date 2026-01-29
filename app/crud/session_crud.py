# crud/session_crud.py
from sqlalchemy.orm import Session
from datetime import datetime
from ..models.session_model import Session, SetLog
from ..schemas.session_schema import SessionCreate, SetLogCreate


def create_session(db: Session, session_create: SessionCreate, user_id: int) -> Session:
    db_session = Session(
        user_id=user_id,
        workout_id=session_create.workout_id,
        start_time=datetime.utcnow(),
        completed=False
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


def update_session_end(db: Session, session_id: int) -> Session | None:
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session or session.completed:
        return None

    session.end_time = datetime.utcnow()
    session.completed = True
    db.commit()
    db.refresh(session)
    return session


def create_set_log(db: Session, log_create: SetLogCreate, session_id: int) -> SetLog:
    db_log = SetLog(
        session_id=session_id,
        exercise_name=log_create.exercise_name,
        set_number=log_create.set_number,
        reps_done=log_create.reps_done,
        weight_used=log_create.weight_used,
        notes=log_create.notes
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log