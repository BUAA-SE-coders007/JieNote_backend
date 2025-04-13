from fastapi.security import OAuth2PasswordBearer
from jwt import PyJWTError, decode
from app.core.config import settings
from fastapi import Depends, HTTPException
# 配置 OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=401, detail="Invalid authentication credentials"
            )
        return {"email": email}
    except PyJWTError:
        raise HTTPException(
            status_code=401, detail="Invalid authentication credentials"
        )