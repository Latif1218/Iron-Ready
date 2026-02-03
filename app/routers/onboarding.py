from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..utils.age_cal import calculate_age
from ..database import get_db
from ..authentication.user_auth import get_current_user
from ..models.user_model import User
from ..models.onboarding_model import Onboarding
from ..schemas.onboarding_schema import SportCategorySelect, SportSubCategorySelect, PersonalInfo, OnboardingCompleteData
from ..crud.onboarding_crud import get_or_create_onboarding


router = APIRouter(
    prefix="/onboarding",
    tags=["Onboarding"]
)


@router.patch("/sport-category", status_code=status.HTTP_200_OK)
def select_sport_category(
    data: SportCategorySelect,
    db: Session = Depends(get_db),
    current_user: Session = Depends(get_current_user)
):
    onboarding = get_or_create_onboarding(db, current_user.id)
    onboarding.sport_category = data.sport_category
    onboarding.sport_sub_category = None  

    db.commit()
    db.refresh(onboarding)

    return {
        "message": "Sport category selected",
        "next_step": "sub_category" if data.sport_category == "Combat" else "personal_info"
    }
    

@router.patch("/sport-sub-category", status_code=status.HTTP_200_OK)
def select_sport_sub_category(
    data: SportSubCategorySelect,
    db: Session = Depends(get_db),
    current_user:Session = Depends(get_current_user)
):
    onboarding = get_or_create_onboarding(db, current_user.id)
    if onboarding.sport_category != "Combat":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sport sub-category selection is only applicable for 'Combat"
        )

    onboarding.sport_sub_category = data.sport_sub_category

    db.commit()
    db.refresh(onboarding)

    return {"message": "Sub-category selected"}


@router.patch("/personal-info", status_code=status.HTTP_200_OK)
def update_personal_info(
    data: PersonalInfo,
    db: Session = Depends(get_db),
    current_user: Session = Depends(get_current_user)
):
    onboarding = get_or_create_onboarding(db, current_user.id)

    onboarding.birth_date = data.birth_date
    onboarding.gender = data.gender
    onboarding.height_cm = data.height_cm
    onboarding.weight_kg = data.weight_kg
    onboarding.age = calculate_age(data.birth_date)

    db.commit()
    db.refresh(onboarding)

    return {"message": "Personal info updated"}



@router.patch("/complete", status_code=status.HTTP_200_OK)
def complete_onboarding(
    data: OnboardingCompleteData,
    db: Session = Depends(get_db),
    current_user: Session = Depends(get_current_user)
):
    onboarding = get_or_create_onboarding(db, current_user.id)

    onboarding.strength_levels = data.strength_levels
    onboarding.training_days = data.training_days
    onboarding.is_onboarded = True
    onboarding.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(onboarding)

    return {"message": "Onboarding completed successfully"}