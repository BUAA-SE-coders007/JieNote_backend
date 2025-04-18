from fastapi import APIRouter, HTTPException, Depends, UploadFile, Form, File
from app.schemas.user import UserUpdate, PasswordUpdate
from app.curd.user import update_user_in_db, get_user_by_email, update_user_password
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.get_db import get_db
from app.utils.auth import get_current_user
from passlib.context import CryptContext
import os
from uuid import uuid4

router = APIRouter()

# update current user
@router.put("", response_model=dict)
async def update_current_user(
    username: str = Form(None), 
    avatar: UploadFile = File(None), 
    db: AsyncSession = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    """
    Update the current user's information.
    """
    db_user = await get_user_by_email(db, current_user["email"])
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        avatar_url = None
        if avatar:
            avatar_file: UploadFile = avatar
            file_extension = os.path.splitext(avatar_file.filename)[1]
            unique_filename = f"{uuid4()}{file_extension}"
            avatar_dir = os.path.join("app", "static", "avatar")
            avatar_path = os.path.join(avatar_dir, unique_filename)

            # 确保以二进制模式写入文件，避免编码问题
            with open(avatar_path, "wb") as f:
                f.write(await avatar_file.read())

            # 生成 URL 路径
            avatar_url = f"/app/static/avatar/{unique_filename}"

            # 删除旧的头像文件
            if db_user.avatar and db_user.avatar != "/app/static/avatar/default.png":
                old_avatar_path = db_user.avatar.lstrip("/")  # 去掉开头的斜杠
                if os.path.exists(old_avatar_path):
                    os.remove(old_avatar_path)
                

        update_user_response = UserUpdate(
            username=username or db_user.username,
            avatar=avatar_url if avatar_url else db_user.avatar
        )
        await update_user_in_db(db, update_user_response, db_user.id)
        return {"msg": "User updated successfully"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/password", response_model=dict)
async def change_password(
    password_update: PasswordUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    db_user = await get_user_by_email(db, current_user["email"])
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if not pwd_context.verify(password_update.old_password, db_user.password):
        raise HTTPException(status_code=400, detail="Old password is incorrect")

    await update_user_password(db, db_user.id, pwd_context.hash(password_update.new_password))
    return {"msg": "Password changed successfully"}