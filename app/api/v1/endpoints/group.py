from fastapi import APIRouter, Query, Body, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from cryptography.fernet import Fernet
import os
import uuid
from datetime import date, datetime
import json

from app.utils.get_db import get_db
from app.utils.auth import get_current_user
from app.curd.group import crud_create, crud_gen_invite_code, crud_enter_group, crud_modify_basic_info, crud_modify_admin_list, crud_remove_member, crud_leave_group, crud_get_basic_info, crud_get_people_info, crud_get_my_level, crud_all_groups
from app.schemas.group import EnterGroup, LeaveGroup

router = APIRouter()

@router.post("/create", response_model=dict)
async def create(group_name: str = Query(...), group_desc: str = Query(...), group_avatar: UploadFile | None = File(None)
                 , db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    if len(group_name) > 30:
        raise HTTPException(status_code=405, detail="Invalid group name, longer than 30")
    if len(group_desc) > 200:
        raise HTTPException(status_code=405, detail="Invalid group description, longer than 200")
    path = "/lhcos-data/group-avatar/default.png"
    # 存储头像，保留扩展名
    if group_avatar:
        os.makedirs("/lhcos-data/group-avatar", exist_ok=True)
        ext = os.path.splitext(group_avatar.filename)[1]
        path = f"/lhcos-data/group-avatar/{uuid.uuid4()}{ext}"
        with open(path, "wb") as f:
            content = await group_avatar.read()
            f.write(content)
    await crud_create(user.get("id"), group_name, group_desc, path, db)
    return {"msg": "Group created successfully"}

@router.get("/genInviteCode", response_model=dict)
async def gen_invite_code(user_email: str = Query(...), group_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    await crud_gen_invite_code(user_email, db)
    today = date.today()
    data = {
        "email": user_email,
        "group_id": group_id,
        "date": today.isoformat()
    }
    json_data = json.dumps(data).encode()
    fernet = Fernet(os.getenv("FERNET_SECRET_KEY"))
    encrypted = fernet.encrypt(json_data)
    return {"inviteCode": encrypted}

@router.post("/enterGroup", response_model=dict)
async def enter_group(inviteCode: EnterGroup, db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    code = inviteCode.inviteCode
    fernet = Fernet(os.getenv("FERNET_SECRET_KEY"))

    decrypted = fernet.decrypt(code.encode())
    data = json.loads(decrypted)

    user_email = user.get("email")
    invite_email = data["email"]
    if user_email != invite_email:
        raise HTTPException(status_code=405, detail="Not your invite code")
    
    invite_date = datetime.strptime(data["date"], "%Y-%m-%d").date()
    today = date.today()
    if today > invite_date:
        raise HTTPException(status_code=406, detail="Invite Code already expired")
    
    await crud_enter_group(user.get("id"), data["group_id"], db)
    return {"msg": "Enter thr group successfully"}

@router.post("/modifyBasicInfo", response_model=dict)
async def modify_basic_info(group_id: int = Query(...), group_name: str | None = Query(None), group_desc: str | None = Query(None), group_avatar: UploadFile | None = File(None), db: AsyncSession = Depends(get_db)):
    if group_name and len(group_name) > 30:
        raise HTTPException(status_code=405, detail="Invalid group name, longer than 30")
    if group_desc and len(group_desc) > 200:
        raise HTTPException(status_code=405, detail="Invalid group description, longer than 200")
    new_path = None
    if group_avatar:
        os.makedirs("/lhcos-data/group-avatar", exist_ok=True)
        # 存储新头像，保留扩展名
        ext = os.path.splitext(group_avatar.filename)[1]
        new_path = f"/lhcos-data/group-avatar/{uuid.uuid4()}{ext}"
        with open(new_path, "wb") as f:
            content = await group_avatar.read()
            f.write(content)
    old_path = await crud_modify_basic_info(db=db, id=group_id, name=group_name, desc=group_desc, avatar=new_path)
    if group_avatar and old_path != "/lhcos-data/group-avatar/default.png":
        os.remove(old_path)
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

@router.get("/getBasicInfo", response_model=dict)
async def get_basic_info(group_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    name, desc, avatar = await crud_get_basic_info(group_id, db)
    return {"avatar": avatar, "name": name, "desc": desc}

@router.get("/getPeopleInfo", response_model=dict)
async def get_people_info(group_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    leader, admins, members = await crud_get_people_info(group_id, db)
    return {"leader": leader, "admins": admins, "members": members}

@router.get("/getMyLevel", response_model=dict)
async def get_my_level(group_id: int = Query(...), db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    user_id = user.get("id")
    level = await crud_get_my_level(user_id, group_id, db)
    return {"level": level}

@router.get("/allGroups", response_model=dict)
async def all_groups(db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    user_id = user.get("id")
    leader, admin, member = await crud_all_groups(user_id, db)
    return {"leader": leader, "admin": admin, "member": member}