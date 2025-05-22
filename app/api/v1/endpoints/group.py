from fastapi import APIRouter, Query, Body, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import os

from app.utils.get_db import get_db
from app.utils.auth import get_current_user
from app.curd.group import crud_create, crud_apply_to_enter, crud_get_applications, crud_reply_to_enter
from app.schemas.group import ApplyToEnter

router = APIRouter()

@router.post("/create", response_model=dict)
async def create(group_name: str = Query(...), group_desc: str = Query(...), group_avatar: UploadFile | None = File(None)
                 , db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    if len(group_name) > 30:
        raise HTTPException(status_code=405, detail="Invalid group name, longer than 30")
    if len(group_desc) > 200:
        raise HTTPException(status_code=405, detail="Invalid group description, longer than 200")
    group_id = await crud_create(user.get("id"), group_name, group_desc, db)
    if group_avatar:
        os.makedirs("/lhcos-data/group-avatar", exist_ok=True)
        ext = os.path.splitext(group_avatar.filename)[1]
        path = os.path.join("/lhcos-data/group-avatar", f"{group_id}{ext}")
        with open(path, "wb") as f:
            content = await group_avatar.read()
            f.write(content)
    return {"msg": "Group created successfully"}

@router.post("/applyToEnter", response_model=dict)
async def apply_to_enter(model: ApplyToEnter, db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    group_id = model.group_id
    user_id = user.get("id")
    await crud_apply_to_enter(user_id, group_id, db)
    return {"msg": "Application sent successfully"}

@router.get("/getApplications", response_model=dict)
async def get_applications(group_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    users = await crud_get_applications(group_id, db)
    return {"users": users}

@router.post("/replyToEnter", response_model=dict)
async def reply_to_enter(user_id: int = Body(...), group_id: int = Body(...), reply: int = Body(...), db: AsyncSession = Depends(get_db)):
    if reply != 0 and reply != 1:
        raise HTTPException(status_code=405, detail="Wrong parameter, reply should be either 0 or 1")
    msg = await crud_reply_to_enter(user_id, group_id, reply, db)
    return {"msg": msg}