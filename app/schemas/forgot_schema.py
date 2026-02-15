from pydantic import BaseModel, EmailStr, Field, field_validator
class ForgotPasswordRequest(BaseModel):
    email: EmailStr
    model_config = {
        "extra" : "forbid"
    }
class OTPVerify(BaseModel):
    email: EmailStr
    otp: str
    model_config = {
        "extra" : "forbid"
    }
    @field_validator('otp')
    def validate_otp(cls, v):
        if not v.isdigit():
            raise ValueError('OTP most contain only digits')
        return v
class PasswordUpdate(BaseModel):
    new_password: str = Field(..., min_length=8, max_length=128, description="password must be between 8 to 128 characters")
    model_config = {
        "extra": "forbid"
    }
class PasswoedUpdateWithoutToken(BaseModel):
    email : EmailStr
    otp : str
    new_password: str = Field(..., min_length=8, max_length=128, description="password must be between 8 to 128 characters")
    model_config = {
        "extra": "forbid"
    }