from fastapi import HTTPException, status, APIRouter, Depends
from ..models import user_model
from ..schemas import user_schema
from sqlalchemy.orm import Session
from ..database import get_db
from ..utils import hashing
from typing import Annotated



router = APIRouter(
    prefix="/register_user",
    tags=["Registration"]
)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=user_schema.UserRespons)
def create_user(
    user: user_schema.UserCreate,
    db: Annotated[Session, Depends(get_db)]
):
    if db.query(user_model.User).filter(user_model.User.email == user.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
        
    hashed_password = hashing.hash_password(user.password)
    user.password = hashed_password
    new_user = user_model.User(**user.model_dump())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
    