from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class UserResponse(BaseModel):
    id: int
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)