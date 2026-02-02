from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..authentication.user_auth import get_current_user
from ..schemas.recovery_schema import RecoveryOut
from ..crud import recovery_crud



router = APIRouter(
    prefix="/recoveries",
    tags=["Recoveries"]
)


@router.get("/", response_model=List[RecoveryOut], status_code=status.HTTP_200_OK)
def get_recoveries(
    db: Session = Depends(get_db),
    current_user: Session = Depends(get_current_user)
):
    recoveries = recovery_crud.get_user_recoveries(db, current_user.id)
    return recoveries


