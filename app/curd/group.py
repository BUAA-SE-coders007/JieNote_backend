from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, delete, update
from app.models.model import User, Group, Folder, Article, Note, Tag, user_group

async def crud_create(leader: int, name: str, description: str, db: AsyncSession):
    new_group = Group(leader=leader, name=name, description=description)
    db.add(new_group)
    await db.commit()
    await db.refresh(new_group)
    return new_group.id

async def crud_gen_invite_code(user_email: str, db: AsyncSession):
    # 检查邮箱存在性
    query = select(User.id).where(User.email == user_email)
    result = await db.execute(query)
    user_id = result.scalar_one_or_none()
    if not user_id:
        raise HTTPException(status_code=405, detail="User not existed")

async def crud_enter_group(user_id: int, group_id: int, db: AsyncSession):
    # 检查是否已经在组织内
    # 已经是组织leader
    query = select(Group).where(Group.id == group_id, Group.leader == user_id)
    result = await db.execute(query)
    group = result.scalar_one_or_none()
    # 已经是组织admin或member
    query = select(user_group).where(user_group.c.user_id == user_id, user_group.c.group_id == group_id)
    result = await db.execute(query)
    row = result.first()
    if group or row:
        raise HTTPException(status_code=408, detail="You are already in the group")
    
    new_relation = insert(user_group).values(user_id=user_id, group_id=group_id)
    await db.execute(new_relation)
    await db.commit()

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

async def crud_get_basic_info(group_id: int, db: AsyncSession):
    query = select(Group.name, Group.description).where(Group.id == group_id)
    result = await db.execute(query)
    group = result.first()
    return group.name, group.description

async def crud_get_people_info(group_id: int, db: AsyncSession):
    # 创建者信息
    query = select(Group.leader).where(Group.id == group_id)
    result = await db.execute(query)
    leader_id = result.scalar_one_or_none()
    query = select(User).where(User.id == leader_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    leader = {"id": user.id, "name": user.username, "avatar": user.avatar}

    # 管理者信息
    query = select(user_group.c.user_id).where(user_group.c.group_id == group_id, user_group.c.is_admin == True)
    result = await db.execute(query)
    admin_ids = result.scalars().all()
    query = select(User).where(User.id.in_(admin_ids))
    result = await db.execute(query)
    users = result.scalars().all()
    admins = [{"id": user.id, "name": user.username, "avatar": user.avatar} for user in users]
    
    # 普通成员信息
    query = select(user_group.c.user_id).where(user_group.c.group_id == group_id, user_group.c.is_admin == False)
    result = await db.execute(query)
    member_ids = result.scalars().all()
    query = select(User).where(User.id.in_(member_ids))
    result = await db.execute(query)
    users = result.scalars().all()
    members = [{"id": user.id, "name": user.username, "avatar": user.avatar} for user in users]
    
    return leader, admins, members

async def crud_get_my_level(user_id: int, group_id: int, db: AsyncSession):
    # 是否是创建者
    query = select(Group.leader).where(Group.id == group_id)
    result = await db.execute(query)
    leader_id = result.scalar_one_or_none()
    if user_id == leader_id:
        return 1
    query = select(user_group).where(user_group.c.user_id == user_id, user_group.c.group_id == group_id)
    result = await db.execute(query)
    relation = result.first()       # relation[0] relation[1] relation[2] 分别为表的第1、2、3列
    # 是否是管理员
    if relation and relation[2]:
        return 2
    # 是否是普通成员
    if relation:
        return 3
    # 未加入组织
    return 4