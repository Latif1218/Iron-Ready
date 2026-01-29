from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List, Optional, Dict
from datetime import datetime, date

class UserBase(BaseModel):
    id: int
    name: str
    email: EmailStr
    age: Optional[int]
    gender: Optional[str]
    height: Optional[float]
    weight: Optional[float]
    sport: Optional[str]
    strength_levels: Optional[Dict]
    training_days: Optional[List[str]]
    
    
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128, description="password must be between 8 to 128 characters")
    role: str = "user"
    
    @field_validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v
    
    
class UserRespons(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime
    
    model_config = {
        "from_attributes": True
    } 
    
    
    
class UserToken(BaseModel):
    access_token : str
    token_type : str

    model_config = {
        "from_attributes": True
    }
    
class TokenData(BaseModel):
    id : Optional[int] = None
    
    
class OnboardingData(BaseModel):
    birth_date: date                 
    gender: str = Field(..., pattern="^(male|female|other|prefer_not_to_say)$")
    height: float = Field(..., gt=100, lt=250)   
    weight: float = Field(..., gt=30, lt=200)   
    sport: str
    strength_levels: Dict[str, float]       
    training_days: List[str]                    

    class Config:
        extra = "forbid"
    
    

class UserUpdate(UserBase):
    pass