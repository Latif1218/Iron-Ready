from sqlalchemy.orm import Session
from ..models.notification_model import Notification
from ..schemas.notification_schema import NotificationCreate


def create_notification(db: Session, notification_create: NotificationCreate, user_id: int) -> Notification:
    db_notification = Notification(
        user_id=user_id,
        message=notification_create.message,
        is_read=False
    )
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification


def get_user_notifications(db: Session, user_id: int, unread_only: bool = False) -> list[Notification]:
    query = db.query(Notification).filter(Notification.user_id == user_id)
    
    if unread_only:
        query = query.filter(Notification.is_read == False)
    
    return query.order_by(Notification.created_at.desc()).all()


def mark_notification_read(db: Session, notification_id: int, user_id: int) -> Notification | None:
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user_id
    ).first()

    if not notification:
        return None

    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification