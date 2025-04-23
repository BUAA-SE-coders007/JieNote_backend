from pydantic import BaseModel

class UserUpdate(BaseModel):
    username: str | None = None
    avatar: str | None = None
    address: str | None = None
    university: str | None = None
    introduction: str | None = None

class PasswordUpdate(BaseModel):
    old_password: str
    new_password: str

