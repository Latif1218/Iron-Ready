from typing import Annotated, List
from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session

from ..authentication.user_auth import get_current_user
from app.database import get_db
from ..models.user_model import User
from ..schemas.notification_schema import NotificationOut
from app.crud import notification_crud

router = APIRouter()

@router.get("/notifications", response_model=List[NotificationOut])
def get_notifications(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    unread_only: bool = False,
) -> List[NotificationOut]:
    return notification_crud.get_user_notifications(
        db=db,
        user_id=current_user.id,
        unread_only=unread_only
    )