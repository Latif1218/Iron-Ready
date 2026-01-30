from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..authentication.user_auth import get_current_user
from ..schemas.notification_schema import NotificationOut
from ..crud import notification_crud



router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)





@router.get("/notifications", response_model=List[NotificationOut])
def get_notifications(
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user:Session = Depends(get_current_user)
):
    return notification_crud.get_user_notifications(db, current_user.id, unread_only=unread_only)