from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, insert, delete, update
from app.models.model import User, Group, Folder, Article, Note, Tag, user_group, enter_application

async def crud_create(leader: int, name: str, description: str, db: AsyncSession):
    new_group = Group(leader=leader, name=name, description=description)
    db.add(new_group)
    await db.commit()
    await db.refresh(new_group)
    return new_group.id

async def crud_apply_to_enter(user_id: int, group_id: int, db: AsyncSession):
    # 是否已经在组织中
    query = select(user_group).where(user_group.c.user_id == user_id, user_group.c.group_id == group_id)
    result = await db.execute(query)
    existing = result.first()
    if existing:
        raise HTTPException(status_code=405, detail="Already in the group")
    query = select(Group).where(Group.id == group_id)
    result = await db.execute(query)
    group = result.scalar_one_or_none()
    if group.leader == user_id:
        raise HTTPException(status_code=405, detail="Already in the group")
    
    # 插入申请表，若已存在申请则抛出异常
    query = insert(enter_application).values(user_id=user_id, group_id=group_id)
    try:
        await db.execute(query)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=405, detail="Don't apply repeatedly")
    
async def crud_get_applications(group_id: int, db: AsyncSession):
    query = select(User.id, User.username).where(User.id.in_(
        select(enter_application.c.user_id).where(enter_application.c.group_id == group_id)
    ))
    result = await db.execute(query)
    users = result.all()
    return [{"user_id": user.id, "user_name": user.username} for user in users]

async def crud_reply_to_enter(user_id: int, group_id: int, reply: bool, db: AsyncSession):
    # 答复后，需要从待处理申请的表中删除表项
    query = delete(enter_application).where(enter_application.c.user_id == user_id, enter_application.c.group_id == group_id)
    result = await db.execute(query)
    if result.rowcount == 0:  # 如果没有删除任何行，说明不存在该项
        raise HTTPException(status_code=405, detail="Application is not existed or already handled")
    await db.commit()

    if reply:
        new_relation = insert(user_group).values(user_id=user_id, group_id=group_id)
        await db.execute(new_relation)
        await db.commit()
        return "Add new member successfully"
    
    return "Refuse the application successfully"

async def crud_modify_basic_info(db: AsyncSession, id: int, name: str | None = None, desc: str | None = None):
    update_data = {}
    if name:
        update_data["name"] = name
    if desc:
        update_data["description"] = desc
    query = update(Group).where(Group.id == id).values(**update_data)
    await db.execute(query)
    await db.commit()

async def crud_modify_admin_list(group_id: int, user_id: int, add_admin: bool, db: AsyncSession):
    # 检查组织中是否有该成员
    query = select(user_group).where(user_group.c.user_id == user_id, user_group.c.group_id == group_id)
    result = await db.execute(query)
    relation = result.first()
    if not relation:
        raise HTTPException(status_code=405, detail="User currently not in the group")
    
    # 将该成员设为或取消管理员
    query = update(user_group).where(user_group.c.group_id == group_id, user_group.c.user_id == user_id).values(is_admin=add_admin)
    await db.execute(query)
    await db.commit()

    return "The user is an admin now" if add_admin else "The user is not an admin now"

async def crud_remove_member(group_id: int, user_id: int, db: AsyncSession):    
    # 不必先检查组织中是否有该成员，若没有则再执行一次delete也不会报错
    query = delete(user_group).where(user_group.c.group_id == group_id, user_group.c.user_id == user_id)
    await db.execute(query)
    await db.commit()

async def crud_leave_group(group_id: int, user_id: int, db: AsyncSession):
    # 不必先检查组织中是否有该成员，若没有则再执行一次delete也不会报错
    query = delete(user_group).where(user_group.c.group_id == group_id, user_group.c.user_id == user_id)
    await db.execute(query)
    await db.commit()