from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    code: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserSendCode(BaseModel):
    email: EmailStr

class ReFreshToken(BaseModel):
    refresh_token: str