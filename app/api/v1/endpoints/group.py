from fastapi import APIRouter, Query, Body, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import os
import glob

from app.utils.get_db import get_db
from app.utils.auth import get_current_user
from app.curd.group import crud_create, crud_apply_to_enter, crud_get_applications, crud_reply_to_enter, crud_modify_basic_info, crud_modify_admin_list, crud_remove_member, crud_leave_group
from app.schemas.group import ApplyToEnter, LeaveGroup

router = APIRouter()

@router.post("/create", response_model=dict)
async def create(group_name: str = Query(...), group_desc: str = Query(...), group_avatar: UploadFile | None = File(None)
                 , db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    if len(group_name) > 30:
        raise HTTPException(status_code=405, detail="Invalid group name, longer than 30")
    if len(group_desc) > 200:
        raise HTTPException(status_code=405, detail="Invalid group description, longer than 200")
    group_id = await crud_create(user.get("id"), group_name, group_desc, db)
    # 存储头像，文件名为 {group_id}.上传文件的扩展名
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
async def reply_to_enter(user_id: int = Body(...), group_id: int = Body(...), reply: bool = Body(...), db: AsyncSession = Depends(get_db)):
    msg = await crud_reply_to_enter(user_id, group_id, reply, db)
    return {"msg": msg}

@router.post("/modifyBasicInfo", response_model=dict)
async def modify_basic_info(group_id: int = Query(...), group_name: str | None = Query(None), group_desc: str | None = Query(None), group_avatar: UploadFile | None = File(None), db: AsyncSession = Depends(get_db)):
    if group_name and len(group_name) > 30:
        raise HTTPException(status_code=405, detail="Invalid group name, longer than 30")
    if group_desc and len(group_desc) > 200:
        raise HTTPException(status_code=405, detail="Invalid group description, longer than 200")
    await crud_modify_basic_info(db=db, id=group_id, name=group_name, desc=group_desc)
    if group_avatar:
        os.makedirs("/lhcos-data/group-avatar", exist_ok=True)
        # 若之前存储了旧头像，则将其删除；若之前就没头像，则不做处理
        old_avatar = glob.glob(os.path.join("/lhcos-data/group-avatar", group_id + ".*"))   # 基本名为group_id的文件列表，最多有一个元素
        if old_avatar:
            os.remove(old_avatar[0])
        # 存储新头像，文件名为 {group_id}.上传文件的扩展名
        ext = os.path.splitext(group_avatar.filename)[1]
        path = os.path.join("/lhcos-data/group-avatar", f"{group_id}{ext}")
        with open(path, "wb") as f:
            content = await group_avatar.read()
            f.write(content)
    return {"msg": "Basic info modified successfully"}

@router.post("/modifyAdminList", response_model=dict)
async def modify_admin_list(group_id: int = Body(...), user_id: int = Body(...), add_admin: bool = Body(...), db: AsyncSession = Depends(get_db)):
    msg = await crud_modify_admin_list(group_id, user_id, add_admin, db)
    return {"msg": msg}

@router.post("/removeMember", response_model=dict)
async def remove_member(group_id: int = Body(...), user_id: int = Body(...), db: AsyncSession = Depends(get_db)):
    await crud_remove_member(group_id, user_id, db)
    return {"msg": "Member removed successfully"}

@router.post("/leaveGroup", response_model=dict)
async def leave_group(model: LeaveGroup, db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    group_id = model.group_id
    user_id = user.get("id")
    await crud_leave_group(group_id, user_id, db)
    return {"msg": "You successfully left the group"}

# 写返回个人文件树的后端时记得加 visible = True