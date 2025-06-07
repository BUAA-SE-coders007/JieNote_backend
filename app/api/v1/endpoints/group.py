from fastapi import APIRouter, Query, Body, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from cryptography.fernet import Fernet
from typing import Optional, List
import os
import uuid
from datetime import date, datetime
import json

from app.utils.get_db import get_db
from app.utils.auth import get_current_user
from app.curd.group import crud_create, crud_gen_invite_code, crud_enter_group, crud_modify_basic_info, crud_modify_admin_list, crud_remove_member, crud_leave_group, crud_get_basic_info, crud_get_people_info, crud_get_my_level, crud_all_groups, crud_new_folder, crud_new_article, crud_new_note, crud_article_tags, crud_file_tree, crud_permission_define, crud_apply_to_delete, crud_all_delete_applications, crud_reply_to_delete, crud_delete, crud_get_permissions, crud_if_edit_note, crud_logs, crud_disband, crud_change_folder_name, crud_change_article_name, crud_change_note, crud_read_note
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
async def modify_basic_info(group_id: int = Query(...), group_name: str | None = Query(None), group_desc: str | None = Query(None), group_avatar: UploadFile | None = File(None), db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
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
    user_id=user.get("id")
    old_path = await crud_modify_basic_info(db=db, id=group_id, user_id=user_id, name=group_name, desc=group_desc, avatar=new_path)
    if group_avatar and old_path != "/lhcos-data/group-avatar/default.png":
        os.remove(old_path)
    return {"msg": "Basic info modified successfully"}

@router.post("/modifyAdminList", response_model=dict)
async def modify_admin_list(group_id: int = Body(...), user_id: int = Body(...), add_admin: bool = Body(...), db: AsyncSession = Depends(get_db)):
    msg = await crud_modify_admin_list(group_id, user_id, add_admin, db)
    return {"msg": msg}

@router.post("/removeMember", response_model=dict)
async def remove_member(group_id: int = Body(...), user_id: int = Body(...), db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    remover_id = user.get("id")
    await crud_remove_member(group_id, remover_id, user_id, db)
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

@router.post("/newFolder", response_model=dict)
async def new_folder(group_id: int = Body(...), folder_name: str = Body(...), db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    if len(folder_name) > 30:
        raise HTTPException(status_code=405, detail="Invalid folder name, longer than 30")
    user_id = user.get("id")
    folder_id = await crud_new_folder(user_id, group_id, folder_name, db)
    return {"msg": "Folder created successfully", "folder_id": folder_id}

@router.post("/newArticle", response_model=dict)
async def new_article(folder_id: int = Query(...), article: UploadFile = File(...), db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    # 检查上传的必须为 PDF
    head = await article.read(5)                    # 读取文件的前 5 个字节，用于魔数检测
    if not head.startswith(b"%PDF-"):
        raise HTTPException(status_code=405, detail="File uploaded must be a PDF.")
    await article.seek(0)                           # 重置文件指针位置
    # 存储到云存储位置
    os.makedirs("/lhcos-data", exist_ok=True)
    url = f"/lhcos-data/{uuid.uuid4()}.pdf"
    with open(url, "wb") as f:
        content = await article.read()
        f.write(content)
    # 用文件名（不带扩展名）作为 Article 名称
    name = os.path.splitext(article.filename)[0] 
    # 新建 Article 记录
    user_id = user.get("id")
    article_id = await crud_new_article(user_id, folder_id, name, url, db)    

    return {"msg": "Article created successfully", "article_id": article_id}

@router.post("/newNote", response_model=dict)
async def new_note(article_id: int = Body(...), title: str = Body(...), content: str = Body(...), db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    if len(title) > 100:
        raise HTTPException(status_code=405, detail="Invalid note title, longer than 100")
    user_id = user.get("id")
    note_id = await crud_new_note(article_id, title, content, user_id, db)
    return {"msg": "Note created successfully", "note_id": note_id}

@router.post("/articleTags", response_model=dict)
async def article_tags(article_id: int = Body(...), tag_contents: List[str] = Body(...), db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    for tag_content in tag_contents:
        if len(tag_content) > 30:
            raise HTTPException(status_code=405, detail="Invalid tag content existed, longer than 30")
    user_id = user.get("id")
    await crud_article_tags(article_id, user_id, tag_contents, db)
    return {"msg": "Tags and order changed successfully"}

@router.get("/fileTree", response_model=dict)
async def file_tree(group_id: int = Query(...), page_number: Optional[int] = Query(None, ge=1), page_size: Optional[int] = Query(None, ge=1), db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    user_id = user.get("id")
    total_folder_num, folders = await crud_file_tree(group_id, user_id, page_number, page_size, db)
    return {"total_folder_num": total_folder_num, "folders": folders}

@router.post("/permissionDefine", response_model=dict)
async def permission_define(group_id: int = Body(...), user_id: int = Body(...), item_type: int = Body(...), item_id: int = Body(...), permission: int = Body(...), db: AsyncSession = Depends(get_db)):
    await crud_permission_define(group_id, user_id, item_type, item_id, permission, db)
    return {"msg": "Permission defined successfully"}

@router.post("/applyToDelete", response_model=dict)
async def apply_to_delete(group_id: int = Body(...), item_type: int = Body(...), item_id: int = Body(...), db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    user_id = user.get("id")
    await crud_apply_to_delete(group_id, user_id, item_type, item_id, db)
    return {"msg": "Delete application sent successfully"}

@router.get("/allDeleteApplications", response_model=dict)
async def all_delete_applications(group_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    applications = await crud_all_delete_applications(group_id, db)
    return {"applications": applications}

@router.post("/replyToDelete", response_model=dict)
async def reply_to_delete(item_type: int = Body(...), item_id: int = Body(...), agree: bool = Body(...), db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    user_id = user.get("id")
    msg, article_urls = await crud_reply_to_delete(user_id, item_type, item_id, agree, db)
    for article_url in article_urls:
        os.remove(article_url)
    return {"msg": msg}

@router.delete("/delete", response_model=dict)
async def delete(item_type: int = Body(...), item_id: int = Body(...), db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    user_id = user.get("id")
    article_urls = await crud_delete(user_id, item_type, item_id, db)
    for article_url in article_urls:
        os.remove(article_url)
    return {"msg": "Item and its child nodes deleted forever successfully"}

@router.get("/getPermissions", response_model=dict)
async def get_permissions(group_id: int = Query(...), item_type: int = Query(...), item_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    unaccessible, read_only, writeable = await crud_get_permissions(group_id, item_type, item_id, db)
    return {"unaccessible": unaccessible, "read_only": read_only, "writeable":  writeable}

@router.get("/ifEditNote", response_model=dict)
async def if_edit_note(note_id: int = Query(...), db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    user_id = user.get("id")
    editable = await crud_if_edit_note(note_id, user_id, db)
    return {"editable": editable}

@router.post("/changeFolderName", response_model=dict)
async def change_folder_name(folder_id: int = Body(...), folder_name: str = Body(...), db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    if len(folder_name) > 30:
        raise HTTPException(status_code=405, detail="Invalid folder name, longer than 30")
    user_id = user.get("id")
    await crud_change_folder_name(folder_id, folder_name, user_id, db)
    return {"msg": "Folder name changed successfully"}

@router.post("/changeArticleName", response_model=dict)
async def change_article_name(article_id: int = Body(...), article_name: str = Body(...), db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    user_id = user.get("id")
    await crud_change_article_name(article_id, article_name, user_id, db)
    return {"msg": "Article name changed successfully"}

@router.post("/changeNote", response_model=dict)
async def change_note(note_id: int = Body(...), note_title: Optional[str] = Body(default=None), note_content: Optional[str] = Body(default=None), db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    if note_title and len(note_title) > 100:
        raise HTTPException(status_code=405, detail="Invalid note title, longer than 100")
    user_id = user.get("id")
    await crud_change_note(user_id, note_id, note_title, note_content, db)
    return {"msg": "Note changed successfully"}

@router.get("/readNote", response_model=dict)
async def read_note(note_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    note_content, update_time = await crud_read_note(note_id, db)
    return {"note_content": note_content, "update_time": update_time}

@router.get("/logs", response_model=dict)
async def logs(group_id: int = Query(...), page_number: Optional[int] = Query(None, ge=1), page_size: Optional[int] = Query(None, ge=1), db: AsyncSession = Depends(get_db)):
    total_num, return_value = await crud_logs(group_id, page_number, page_size, db)
    return {"total_num": total_num, "logs": return_value}

@router.delete("/disband", response_model=dict)
async def disband(group_id: int, db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    user_id = user.get("id")
    article_urls, avatar_url = await crud_disband(group_id, user_id, db)
    for article_url in article_urls:
        os.remove(article_url)
    if avatar_url != "/lhcos-data/group-avatar/default.png":
        os.remove(avatar_url)
    return {"msg": "Group disbanded successfully"}


from app.curd.article import get_article_info_in_db_by_id, crud_upload_to_self_folder
@router.put("/copy", response_model=dict)
async def copy_article(folder_id: int, article_id: int, is_group: Optional[bool] = None, db : AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    """
    Copy an article file by its ID to a specified directory.
    """
    # 根据 ID 查询文章信息
    file_path, title = await get_article_info_in_db_by_id(db=db, article_id=article_id)
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")
    
    old_file_path = file_path
    
    if is_group is not None and is_group is True:
        # 表示从群组转存到个人目录
        new_article_id = await crud_new_article(
            user_id= user.get("id"),
            folder_id=folder_id,
            article_name=title,
            url=old_file_path,
            db=db
        )
        return {"msg": "Article copied successfully", "new_article_id": new_article_id}
    else:
        new_article_id = await crud_upload_to_self_folder(
            name=title, 
            folder_id=folder_id, 
            url=old_file_path, 
            db=db
        )
        return {"msg": "Article copied successfully", "new_article_id": new_article_id}
