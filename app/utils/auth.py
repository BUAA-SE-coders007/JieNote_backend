from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException
from jose import JWTError, jwt  # 用 jose 替代 jwt
from app.core.config import settings

# 配置 OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        user_id: int = payload.get("id")
        if email is None or user_id is None:
            raise HTTPException(
                status_code=401, detail="Invalid authentication credentials"
            )
        return {"email": email, "id": user_id}
    except JWTError:
        raise HTTPException(
            status_code=401, detail="Invalid authentication credentials"
        )