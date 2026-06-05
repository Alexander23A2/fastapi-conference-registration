from datetime import date
from pydantic import BaseModel, EmailStr, Field, field_validator

class UserBase(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=50)
    last_name: str = Field(..., min_length=2, max_length=50)
    gender: str = Field(..., description="Чоловіча / Жіноча / Інше")
    nationality: str = Field(..., min_length=2)
    organization: str = Field(..., min_length=2)
    position: str = Field(..., min_length=2)
    birth_date: date
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Паролі не збігаються")
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True