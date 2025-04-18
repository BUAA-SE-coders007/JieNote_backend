from pydantic import BaseModel

class UserUpdate(BaseModel):
    username: str | None = None
    avatar: str | None = None

class PasswordUpdate(BaseModel):
    old_password: str
    new_password: str

