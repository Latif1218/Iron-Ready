from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..schemas import user_schema
from ..database import get_db
from ..authentication import user_auth
from ..utils import age_cal
from datetime import datetime



router = APIRouter(
    prefix="/onboarding",
    tags=["Onboarding"]
)


@router.patch("/onboarding", status_code=status.HTTP_200_OK, response_model=user_schema.UserRespons)
def complete_onboarding(
    data: user_schema.OnboardingData,
    current_user: Session = Depends(user_auth.get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.is_onboarded:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has already completed onboarding."
        )
    calculated_age = age_cal.calculate_age(data.birth_date)
    
    update_data = data.dict(exclude_unset=True)
    update_data["age"] = calculated_age
    update_data["is_onboarded"] = True
    update_data["onboarding_completed_at"] = datetime.utcnow()
    
    
    update_user = user_auth.update_user(
        db, 
        current_user.id, 
        update_data
    )
    
    if not update_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
    
    return update_user