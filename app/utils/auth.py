from fastapi.security import OAuth2PasswordBearer
from jwt import PyJWTError, decode
from app.core.config import settings
from fastapi import Depends, HTTPException
import asyncio

# 配置 OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        loop = asyncio.get_event_loop()
        payload = await loop.run_in_executor(
            None, decode, token, settings.SECRET_KEY, [settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        user_id: int = payload.get("id")  # 从 payload 中提取用户 ID
        if email is None or user_id is None:
            raise HTTPException(
                status_code=401, detail="Invalid authentication credentials"
            )
        return {"email": email, "id": user_id}  # 返回用户 ID 和 email
    except PyJWTError:
        raise HTTPException(
            status_code=401, detail="Invalid authentication credentials"
        )