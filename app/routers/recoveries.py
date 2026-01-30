from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated, List

from ..database import get_db
from ..authentication.user_auth import get_current_user
from ..models.user_model import User
from ..schemas.recovery_schema import RecoveryOut
from ..crud.recovery_crud import get_user_recoveries



router = APIRouter(
    prefix="/recoveries",
    tags=["Recoveries"]
)


@router.get("/", response_model=List[RecoveryOut], status_code=status.HTTP_200_OK)
def get_recoveries(
    db: Session = Depends(get_db),
    current_user: Session = Depends(get_current_user)
):
    if current_user in None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication Failed"
        )
    recoveries = get_user_recoveries(db, current_user.id)
    return recoveries


