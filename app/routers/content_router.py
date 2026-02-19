import os
import uuid
import shutil
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Annotated
from ..database import get_db
from ..authentication.user_auth import get_current_admin_user
from ..models.onboarding_content_model import OnboardingContent
from ..models.user_model import User

router = APIRouter(
    prefix="/content",
    tags=["Content Update"]
)

UPLOAD_DIR = "uploads/onboarding"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png"}
MAX_IMAGE_SIZE = 3 * 1024 * 1024  


@router.put("/{content_id}", response_model=OnboardingContent, status_code=status.HTTP_200_OK)
async def update_onboarding_content(
    content_id: int,
    db: Annotated[Session, Depends(get_db)],
    title: Annotated[str, Form(min_length=1, max_length=200)],
    subtitle: Annotated[str, Form(min_length=1, max_length=500)],
    current_admin: Annotated[User, Depends(get_current_admin_user)],
    image: UploadFile = File(None)
):
    content = db.query(OnboardingContent).filter(
        OnboardingContent.id == content_id
    ).first()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Onboarding co"
        )
    content.title = title.strip()
    content.subtitle = subtitle.strip()

    if image:
        if image.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only JPEG or PNG image are allowed"
            )
        
        image.file.seek(0,2)
        file_size = image.file.tell()
        image.file.seek(0)
        if file_size > MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image size exceeds 3MB limit"
            )
        
        ext = image.filename.split(".")[-1].lower()
        filename = f"{uuid.uuid4()}.{ext}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)


        content.image_url = f"/{file_path}"

    db.commit()
    db.refresh(content)

    return content