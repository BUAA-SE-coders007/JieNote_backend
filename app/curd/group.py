from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, delete, update, not_, exists
from sqlalchemy import func
from app.models.model import User, Group, Folder, Article, Note, Tag, user_group, self_recycle_bin, operate_permissions, delete_applications, group_logs

async def crud_create(leader: int, name: str, description: str, path: str, db: AsyncSession):
    new_group = Group(leader=leader, name=name, description=description, avatar=path)
    db.add(new_group)
    await db.flush()  # 仅将数据同步到数据库，事务尚未提交，此时 new_group.id 已可用
    new_relation = insert(user_group).values(user_id=leader, group_id=new_group.id, level=1)
    await db.execute(new_relation)
    new_log = insert(group_logs).values(group_id=new_group.id, type=0, person1=leader)
    await db.execute(new_log)
    await db.commit()

async def crud_gen_invite_code(user_email: str, db: AsyncSession):
    # 检查邮箱存在性
    query = select(User.id).where(User.email == user_email)
    result = await db.execute(query)
    user_id = result.scalar_one_or_none()
    if not user_id:
        raise HTTPException(status_code=405, detail="User not existed")

async def crud_enter_group(user_id: int, group_id: int, db: AsyncSession):
    # 检查是否已经在组织内
    query = select(user_group).where(user_group.c.user_id == user_id, user_group.c.group_id == group_id)
    result = await db.execute(query)
    exist = result.first()
    if exist:
        raise HTTPException(status_code=408, detail="You are already in the group")   
    new_relation = insert(user_group).values(user_id=user_id, group_id=group_id)
    await db.execute(new_relation)
    new_log = insert(group_logs).values(group_id=group_id, type=1, person1=user_id)
    await db.execute(new_log)
    await db.commit()

async def crud_modify_basic_info(db: AsyncSession, id: int, user_id: int, name: str | None = None, desc: str | None = None, avatar: str | None = None):
    query = select(Group.avatar).where(Group.id == id)
    result = await db.execute(query)
    old_path = result.scalar_one_or_none()
    update_data = {}
    if name:
        update_data["name"] = name
    if desc:
        update_data["description"] = desc
    if avatar:
        update_data["avatar"] = avatar
    query = update(Group).where(Group.id == id).values(**update_data)
    await db.execute(query)
    new_log = insert(group_logs).values(group_id=id, type=2, person1=user_id)
    await db.execute(new_log)
    await db.commit()
    return old_path

async def crud_modify_admin_list(group_id: int, user_id: int, add_admin: bool, db: AsyncSession):
    # 检查组织中是否有该成员
    query = select(user_group).where(user_group.c.user_id == user_id, user_group.c.group_id == group_id)
    result = await db.execute(query)
    relation = result.first()
    if not relation:
        raise HTTPException(status_code=405, detail="User currently not in the group")
    
    # 将该成员设为或取消管理员
    if add_admin:
        query = update(user_group).where(user_group.c.group_id == group_id, user_group.c.user_id == user_id).values(level=2)
        await db.execute(query)
        query = delete(operate_permissions).where(operate_permissions.c.group_id == group_id, operate_permissions.c.user_id == user_id)
        await db.execute(query)
        new_log = insert(group_logs).values(group_id=group_id, type=3, person2=user_id)
        await db.execute(new_log)
    else:
        query = update(user_group).where(user_group.c.group_id == group_id, user_group.c.user_id == user_id).values(level=3)
        await db.execute(query)
        new_log = insert(group_logs).values(group_id=group_id, type=4, person2=user_id)
        await db.execute(new_log)
    await db.commit()

    return "The user is an admin now" if add_admin else "The user is not an admin now"

async def crud_remove_member(group_id: int, user_id: int, remove_member_id: int, db: AsyncSession):
    # 若已无此人，则直接return
    query = select(user_group).where(user_group.c.user_id == remove_member_id, user_group.c.group_id == group_id)
    result = await db.execute(query)
    relation = result.first()
    if not relation:
        return
    # 写日志
    new_log = insert(group_logs).values(group_id=group_id, type=5, person1=user_id, person2=remove_member_id)
    await db.execute(new_log)
    # 删除组织成员记录
    query = delete(user_group).where(user_group.c.group_id == group_id, user_group.c.user_id == remove_member_id)
    await db.execute(query)
    # 清除权限限制和删除申请记录
    query = delete(operate_permissions).where(operate_permissions.c.group_id == group_id, operate_permissions.c.user_id == remove_member_id)
    await db.execute(query)
    query = delete(delete_applications).where(delete_applications.c.group_id == group_id, delete_applications.c.user_id == remove_member_id)
    await db.execute(query)
    await db.commit()

async def crud_leave_group(group_id: int, user_id: int, db: AsyncSession):
    # 若已无此人，则直接return
    query = select(user_group).where(user_group.c.user_id == user_id, user_group.c.group_id == group_id)
    result = await db.execute(query)
    relation = result.first()
    if not relation:
        return
    # 写日志
    new_log = insert(group_logs).values(group_id=group_id, type=6, person1=user_id)
    await db.execute(new_log)
    # 不必先检查组织中是否有该成员，若没有则再执行一次delete也不会报错
    query = delete(user_group).where(user_group.c.group_id == group_id, user_group.c.user_id == user_id)
    await db.execute(query)
    # 清除权限限制和删除申请记录
    query = delete(operate_permissions).where(operate_permissions.c.group_id == group_id, operate_permissions.c.user_id == user_id)
    await db.execute(query)
    query = delete(delete_applications).where(delete_applications.c.group_id == group_id, delete_applications.c.user_id == user_id)
    await db.execute(query)
    await db.commit()

async def crud_get_basic_info(group_id: int, db: AsyncSession):
    query = select(Group.name, Group.description, Group.avatar).where(Group.id == group_id)
    result = await db.execute(query)
    group = result.first()
    return group.name, group.description, group.avatar

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
    query = select(user_group.c.user_id).where(user_group.c.group_id == group_id, user_group.c.level == 2)
    result = await db.execute(query)
    admin_ids = result.scalars().all()
    query = select(User).where(User.id.in_(admin_ids))
    result = await db.execute(query)
    users = result.scalars().all()
    admins = [{"id": user.id, "name": user.username, "avatar": user.avatar} for user in users]
    
    # 普通成员信息
    query = select(user_group.c.user_id).where(user_group.c.group_id == group_id, user_group.c.level == 3)
    result = await db.execute(query)
    member_ids = result.scalars().all()
    query = select(User).where(User.id.in_(member_ids))
    result = await db.execute(query)
    users = result.scalars().all()
    members = [{"id": user.id, "name": user.username, "avatar": user.avatar} for user in users]
    
    return leader, admins, members

async def crud_get_my_level(user_id: int, group_id: int, db: AsyncSession):
    query = select(user_group).where(user_group.c.user_id == user_id, user_group.c.group_id == group_id)
    result = await db.execute(query)
    relation = result.first()
    # 在组织中       
    if relation:
        return relation[2]          # relation[0] relation[1] relation[2] 分别为表的第1、2、3列
    # 不在组织中
    return 4

async def crud_all_groups(user_id: int, db: AsyncSession):
    query = select(Group).where(Group.leader == user_id).order_by(Group.id.desc())
    result = await db.execute(query)
    groups = result.scalars().all()
    leader = [{"group_id": group.id, "group_name": group.name, "group_avatar": group.avatar, "group_desc": group.description} for group in groups]
    
    query = select(user_group.c.group_id).where(user_group.c.user_id == user_id, user_group.c.level == 2)
    result = await db.execute(query)
    group_ids = result.scalars().all()
    query = select(Group).where(Group.id.in_(group_ids)).order_by(Group.id.desc())
    result = await db.execute(query)
    groups = result.scalars().all()
    admin = [{"group_id": group.id, "group_name": group.name, "group_avatar": group.avatar, "group_desc": group.description} for group in groups]

    query = select(user_group.c.group_id).where(user_group.c.user_id == user_id, user_group.c.level == 3)
    result = await db.execute(query)
    group_ids = result.scalars().all()
    query = select(Group).where(Group.id.in_(group_ids)).order_by(Group.id.desc())
    result = await db.execute(query)
    groups = result.scalars().all()
    member = [{"group_id": group.id, "group_name": group.name, "group_avatar": group.avatar, "group_desc": group.description} for group in groups]

    return leader, admin, member

async def crud_new_folder(user_id: int, group_id: int, folder_name: str, db: AsyncSession):
    new_folder = Folder(group_id=group_id, name=folder_name)
    db.add(new_folder)
    new_log = insert(group_logs).values(group_id=group_id, type=7, person1=user_id, folder=folder_name)
    await db.execute(new_log)
    await db.commit()
    await db.refresh(new_folder)
    return new_folder.id

async def crud_new_article(user_id: int, folder_id: int, article_name: str, url: str, db: AsyncSession):
    # 查询必要信息
    query = select(Folder.group_id, Folder.name).where(Folder.id == folder_id)
    result = await db.execute(query)
    folder_info = result.one_or_none()
    group_id, folder_name = folder_info
    # 新建文献记录
    new_article = Article(folder_id=folder_id, name=article_name, url=url, group_id=group_id)
    db.add(new_article)
    # 写日志
    new_log = insert(group_logs).values(group_id=group_id, type=8, person1=user_id, folder=folder_name, article=article_name)
    await db.execute(new_log)

    await db.commit()
    await db.refresh(new_article)
    return new_article.id

async def crud_new_note(article_id: int, title: str, content: str, user_id: int, db: AsyncSession):
    # 查询必要信息
    query = select(Article.name, Article.group_id, Article.folder_id).where(Article.id == article_id)
    result = await db.execute(query)
    article_info = result.one_or_none()
    article_name, group_id, folder_id = article_info
    query = select(Folder.name).where(Folder.id == folder_id)
    result = await db.execute(query)
    folder_name = result.scalar_one_or_none()
    # 新建笔记记录
    new_note = Note(content=content, article_id=article_id, title=title, group_id=group_id)
    db.add(new_note)
    # 写日志
    new_log = insert(group_logs).values(group_id=group_id, type=9, person1=user_id, folder=folder_name, article=article_name, note=title)
    await db.execute(new_log)

    await db.commit()
    await db.refresh(new_note)
    return new_note.id

async def crud_article_tags(article_id: int, user_id: int, tag_contents, db: AsyncSession):
    # 权限检查
    query = select(operate_permissions).where(operate_permissions.c.user_id == user_id, operate_permissions.c.item_type == 2, operate_permissions.c.item_id == article_id)
    result = await db.execute(query)
    relation = result.first()
    if relation:
        raise HTTPException(status_code=403, detail="You have no permission to edit")
    # 查询必要信息
    query = select(Article.name, Article.folder_id, Article.group_id).where(Article.id == article_id)         # 所属文献名
    result = await db.execute(query)
    article_info = result.one_or_none()
    article_name, folder_id, group_id = article_info
    query = select(Folder.name).where(Folder.id == folder_id)                               # 所属文件夹名
    result = await db.execute(query)
    folder_name = result.scalar_one_or_none()
    query = select(Tag).where(Tag.article_id == article_id).order_by(Tag.id.asc())          # 原Tag
    result = await db.execute(query)
    tags = result.scalars().all()
    article_tags = ""
    for i in range(len(tags)):
        article_tags = article_tags + tags[i].content + ", "
    article_tags = article_tags[:-2] if article_tags else "无Tag"
    article_new = ""                                                                        # 修改后Tag
    for i in range(len(tag_contents)):
        article_new = article_new + tag_contents[i] + ", "
    article_new = article_new[:-2] if article_new else "无Tag"
    # 写日志
    new_log = insert(group_logs).values(group_id=group_id, type=12, person1=user_id, folder=folder_name, article=article_name, article_tags=article_tags, article_new=article_new)
    await db.execute(new_log)
    # Tag 修改
    query = delete(Tag).where(Tag.article_id == article_id)
    await db.execute(query)
    await db.commit()
    new_tags = []
    for i in range(0, len(tag_contents)):
        new_tags.append(Tag(content=tag_contents[i], article_id=article_id))
    db.add_all(new_tags)
    await db.commit()
    for i in range(0, len(new_tags)):
        await db.refresh(new_tags[i])

async def crud_file_tree(group_id: int, user_id: int, page_number: int, page_size: int, db: AsyncSession):
    query = select(Folder).where(Folder.group_id == group_id).order_by(Folder.id.desc())
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total_num = count_result.scalar()

    if page_number and page_size:
        offset = (page_number - 1) * page_size
        query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    folders = result.scalars().all()

    folder_array = [{"folder_id": folder.id, "folder_name": folder.name, "articles": []} for folder in folders]
    for i in range(len(folder_array)):
        query = select(Article).where(
            Article.folder_id == folder_array[i].get("folder_id"),
            # 不存在不可见限制
            not_(exists(
                    select(operate_permissions.c.item_id).where(
                        operate_permissions.c.group_id == group_id,
                        operate_permissions.c.user_id == user_id,
                        operate_permissions.c.item_type == 2,
                        operate_permissions.c.item_id == Article.id,
                        operate_permissions.c.accessible == False
                    )
                )
            )
        ).order_by(Article.id.desc())
        result = await db.execute(query)
        articles = result.scalars().all()
        article_array = [{"article_id": article.id, "article_name": article.name, "tags": [], "notes": []} for article in articles]
        folder_array[i]["articles"] = article_array
        for j in range(len(article_array)):
            # 查找所有tag
            query = select(Tag).where(Tag.article_id == article_array[j].get("article_id")).order_by(Tag.id.asc())
            result = await db.execute(query)
            tags = result.scalars().all()
            tag_array = [{"tag_id": tag.id, "tag_content": tag.content} for tag in tags]
            article_array[j]["tags"] = tag_array
            # 查找所有note
            query = select(Note).where(
                Note.article_id == article_array[j].get("article_id"),
            # 不存在不可见限制
                not_(exists(
                        select(operate_permissions.c.item_id).where(
                            operate_permissions.c.group_id == group_id,
                            operate_permissions.c.user_id == user_id,
                            operate_permissions.c.item_type == 3,
                            operate_permissions.c.item_id == Note.id,
                            operate_permissions.c.accessible == False
                        )
                    )
                )
            ).order_by(Note.id.desc())
            result = await db.execute(query)
            notes = result.scalars().all()
            note_array = [{"note_id": note.id, "note_title": note.title} for note in notes]
            article_array[j]["notes"] = note_array
    
    return total_num, folder_array

async def crud_permission_define(group_id: int, user_id: int, item_type: int, item_id: int, permission: int, db: AsyncSession):
    # 检查组织中是否有该成员
    query = select(user_group).where(user_group.c.user_id == user_id, user_group.c.group_id == group_id)
    result = await db.execute(query)
    relation = result.first()
    if not relation:
        raise HTTPException(status_code=405, detail="User currently not in the group")
    if relation[2] != 3:
        raise HTTPException(status_code=405, detail="Permission can only be defined to common members")
    # 可编辑
    if permission == 2:
        query = delete(operate_permissions).where(operate_permissions.c.group_id == group_id, operate_permissions.c.user_id == user_id, operate_permissions.c.item_type == item_type, operate_permissions.c.item_id == item_id)
        await db.execute(query)
        await db.commit()
        return
    # 不可见 0 或仅查看 1
    from sqlalchemy.dialects.mysql import insert  # 用 MySQL 的 insert
    if item_type == 2:
        query = select(Article.folder_id).where(Article.id == item_id)
        result = await db.execute(query)
        folder_id = result.scalar_one_or_none()
        query = insert(operate_permissions).values(group_id=group_id, user_id=user_id, item_type=item_type, item_id=item_id, folder_id=folder_id, accessible=(permission == 1)).on_duplicate_key_update(accessible=(permission == 1))
    if item_type == 3:
        query = select(Note.article_id).where(Note.id == item_id)
        result = await db.execute(query)
        article_id = result.scalar_one_or_none()
        query = select(Article.folder_id).where(Article.id == article_id)
        result = await db.execute(query)
        folder_id = result.scalar_one_or_none()
        query = insert(operate_permissions).values(group_id=group_id, user_id=user_id, item_type=item_type, item_id=item_id, folder_id=folder_id, article_id=article_id, accessible=(permission == 1)).on_duplicate_key_update(accessible=(permission == 1))
    await db.execute(query)
    await db.commit()

async def crud_apply_to_delete(group_id: int, user_id: int, item_type: int, item_id: int, db: AsyncSession):
    if item_type == 3:
        query = select(Note.article_id).where(Note.id == item_id)
        result = await db.execute(query)
        article_id = result.scalar_one_or_none()
        query = select(Article.folder_id).where(Article.id == article_id)
        result = await db.execute(query)
        folder_id = result.scalar_one_or_none()
        # 将申请插入申请表，若已经申请过则什么都不做（IGNORE）
        query = insert(delete_applications).prefix_with("IGNORE").values(
            group_id=group_id,
            user_id=user_id,
            item_type=item_type,
            item_id=item_id,
            article_id=article_id,
            folder_id=folder_id
        )
    if item_type == 2:
        query = select(Article.folder_id).where(Article.id == item_id)
        result = await db.execute(query)
        folder_id = result.scalar_one_or_none()
        # 将申请插入申请表，若已经申请过则什么都不做（IGNORE）
        query = insert(delete_applications).prefix_with("IGNORE").values(
            group_id=group_id,
            user_id=user_id,
            item_type=item_type,
            item_id=item_id,
            folder_id=folder_id
        )
    if item_type == 1:
        # 将申请插入申请表，若已经申请过则什么都不做（IGNORE）
        query = insert(delete_applications).prefix_with("IGNORE").values(
            group_id=group_id,
            user_id=user_id,
            item_type=item_type,
            item_id=item_id,
        )
    await db.execute(query)
    await db.commit()

async def crud_all_delete_applications(group_id: int, db: AsyncSession):
    query = select(
        delete_applications.c.user_id,
        delete_applications.c.item_type,
        delete_applications.c.item_id
    ).where(delete_applications.c.group_id == group_id)
    result = await db.execute(query)
    applications = result.fetchall()

    return_value = []
    for application in applications:
        # 查询申请者name
        query = select(User.username, User.avatar).where(User.id == application.user_id)
        result = await db.execute(query)
        applier = result.one_or_none()
        applier_name, applier_avatar = applier
        # 查询待删除内容的本级名字和上级名字
        if application.item_type == 1:
            # 文件夹名字
            query = select(Folder.name).where(Folder.id == application.item_id)
            result = await db.execute(query)
            folder = result.scalar_one_or_none()
            return_value.append({"applier_name": applier_name, "applier_avatar": applier_avatar, "item_type": 1, "item_id": application.item_id, "folder": folder})
        if application.item_type == 2:
            # 文献名字
            query = select(Article.name, Article.folder_id).where(Article.id == application.item_id)
            result = await db.execute(query)
            article_info = result.one_or_none()
            article, folder_id = article_info
            # 文件夹名字
            query = select(Folder.name).where(Folder.id == folder_id)
            result = await db.execute(query)
            folder = result.scalar_one_or_none()
            return_value.append({"applier_name": applier_name, "applier_avatar": applier_avatar, "item_type": 2, "item_id": application.item_id, "folder": folder, "article": article})
        if application.item_type == 3:
            # 笔记名字
            query = select(Note.title, Note.article_id).where(Note.id == application.item_id)
            result = await db.execute(query)
            note_info = result.one_or_none()
            note, article_id = note_info
            # 文献名字
            query = select(Article.name, Article.folder_id).where(Article.id == article_id)
            result = await db.execute(query)
            article_info = result.one_or_none()
            article, folder_id = article_info
            # 文件夹名字
            query = select(Folder.name).where(Folder.id == folder_id)
            result = await db.execute(query)
            folder = result.scalar_one_or_none()
            return_value.append({"applier_name": applier_name, "applier_avatar": applier_avatar, "item_type": 3, "item_id": application.item_id, "folder": folder, "article": article, "note": note})

    return return_value

async def crud_reply_to_delete(user_id: int, item_type: int, item_id: int, agree: bool, db: AsyncSession):
    # 申请是否已被处理
    query = select(delete_applications).where(delete_applications.c.item_type == item_type, delete_applications.c.item_id == item_id)
    result = await db.execute(query)
    records = result.fetchall()
    if not records:
        return "Application has already been replied, please refresh the page", []
    # 处理
    if agree:
        article_urls = await crud_delete(user_id, item_type, item_id, db)
        return "Agree to delete item and its child nodes forever successfully", article_urls
    query = delete(delete_applications).where(delete_applications.c.item_type == item_type, delete_applications.c.item_id == item_id)
    await db.execute(query)
    await db.commit()
    return "Refuse to delete successfully", []
        
async def crud_delete(user_id: int, item_type: int, item_id: int, db: AsyncSession):
    # 清除删除申请和权限定义
    query = delete(delete_applications).where(delete_applications.c.item_type == item_type, delete_applications.c.item_id == item_id)
    await db.execute(query)
    query = delete(operate_permissions).where(operate_permissions.c.item_type == item_type, operate_permissions.c.item_id == item_id)
    await db.execute(query)
    # 彻底删除文件夹
    if item_type == 1: 
        # 写日志
        query = select(Folder.name, Folder.group_id).where(Folder.id == item_id)
        result = await db.execute(query)
        folder_info = result.one_or_none()
        folder_name, group_id = folder_info
        new_log = insert(group_logs).values(group_id=group_id, type=15, person1=user_id, folder=folder_name)
        await db.execute(new_log)
        # 删除
        query = select(Article.url).where(Article.folder_id == item_id)
        result = await db.execute(query)
        urls = result.scalars().all()
        query = delete(Folder).where(Folder.id == item_id)
        result = await db.execute(query)
        await db.commit()
        return urls
    # 彻底删除文献
    if item_type == 2:
        # 写日志
        query = select(Article.name, Article.url, Article.group_id, Article.folder_id).where(Article.id == item_id) # 组织号和文献名
        result = await db.execute(query)
        article_info = result.one_or_none()
        article_name, url, group_id, folder_id = article_info
        query = select(Folder.name).where(Folder.id == folder_id)                                                   # 文件夹名
        result = await db.execute(query)
        folder_name = result.scalar_one_or_none()
        new_log = insert(group_logs).values(group_id=group_id, type=16, person1=user_id, folder=folder_name, article=article_name)
        await db.execute(new_log)
        # 删除
        query = delete(Article).where(Article.id == item_id)
        result = await db.execute(query)
        await db.commit()
        return [url]
    # 彻底删除笔记
    if item_type == 3:
        # 写日志
        query = select(Note).where(Note.id == item_id)                                          
        result = await db.execute(query)
        note = result.scalar_one_or_none()
        query = select(Article.name, Article.folder_id, Article.group_id).where(Article.id == note.article_id)    # 所属文献名
        result = await db.execute(query)
        article_info = result.one_or_none()
        article_name, folder_id, group_id = article_info
        query = select(Folder.name).where(Folder.id == folder_id)                               # 所属文件夹名
        result = await db.execute(query)
        folder_name = result.scalar_one_or_none()
        new_log = insert(group_logs).values(group_id=group_id, type=17, person1=user_id, folder=folder_name, article=article_name, note=note.title)
        await db.execute(new_log)
        # 删除
        query = delete(Note).where(Note.id == item_id)
        result = await db.execute(query)
        await db.commit()
        return []
    
async def crud_get_permissions(group_id: int, item_type: int, item_id: int, db: AsyncSession):
    # 所有普通成员
    query = select(user_group.c.user_id).where(user_group.c.group_id == group_id, user_group.c.level == 3)
    result = await db.execute(query)
    member_ids = result.scalars().all()
    # 对该实体不可见的普通成员
    query = select(operate_permissions.c.user_id).where(operate_permissions.c.group_id == group_id, operate_permissions.c.item_type == item_type, operate_permissions.c.item_id == item_id, operate_permissions.c.accessible == False)
    result = await db.execute(query)
    unaccessible_ids = result.scalars().all()
    unaccessible = []
    for unaccessible_id in unaccessible_ids:
        query = select(User.username, User.avatar).where(User.id == unaccessible_id)
        result = await db.execute(query)
        user_info = result.one_or_none()
        user_name, user_avatar = user_info
        unaccessible.append({"user_name": user_name, "user_avatar": user_avatar})
    # 对该实体仅查看的普通成员id
    query = select(operate_permissions.c.user_id).where(operate_permissions.c.group_id == group_id, operate_permissions.c.item_type == item_type, operate_permissions.c.item_id == item_id, operate_permissions.c.accessible == True)
    result = await db.execute(query)
    read_only_ids = result.scalars().all()
    read_only = []
    for read_only_id in read_only_ids:
        query = select(User.username, User.avatar).where(User.id == read_only_id)
        result = await db.execute(query)
        user_info = result.one_or_none()
        user_name, user_avatar = user_info
        read_only.append({"user_name": user_name, "user_avatar": user_avatar})
    # 对该实体可编辑的普通成员id
    writeable_ids = []
    for member_id in member_ids:
        if member_id not in set(unaccessible_ids) and member_id not in set(read_only_ids):
            writeable_ids.append(member_id)
    writeable = []
    for writeable_id in writeable_ids:
        query = select(User.username, User.avatar).where(User.id == writeable_id)
        result = await db.execute(query)
        user_info = result.one_or_none()
        user_name, user_avatar = user_info
        writeable.append({"user_name": user_name, "user_avatar": user_avatar})

    return unaccessible, read_only, writeable

async def crud_change_folder_name(folder_id: int, folder_name: str, user_id: int, db: AsyncSession):
    query = select(Folder).where(Folder.id == folder_id)
    result = await db.execute(query)
    folder = result.scalar_one_or_none()
    # 写日志
    new_log = insert(group_logs).values(group_id=folder.group_id, type=10, person1=user_id, folder=folder.name, folder_new=folder_name)
    await db.execute(new_log)
    # 改名字
    folder.name = folder_name
    await db.commit()
    await db.refresh(folder)

async def crud_change_article_name(article_id: int, article_name: str, user_id: int, db: AsyncSession):
    # 权限检查
    query = select(operate_permissions).where(operate_permissions.c.user_id == user_id, operate_permissions.c.item_type == 2, operate_permissions.c.item_id == article_id)
    result = await db.execute(query)
    relation = result.first()
    if relation:
        raise HTTPException(status_code=403, detail="You have no permission to edit")
    # 查询必要信息
    query = select(Article).where(Article.id == article_id)
    result = await db.execute(query)
    article = result.scalar_one_or_none()
    query = select(Folder).where(Folder.id == article.folder_id)
    result = await db.execute(query)
    folder = result.scalar_one_or_none()
    # 写日志
    new_log = insert(group_logs).values(group_id=folder.group_id, type=11, person1=user_id, folder=folder.name, article=article.name, article_new=article_name)
    await db.execute(new_log)
    # 改名字
    article.name = article_name
    await db.commit()
    await db.refresh(article)

async def crud_change_note(user_id: int, note_id: int, note_title: str, note_content: str, db: AsyncSession):
    # 权限检查
    query = select(operate_permissions).where(operate_permissions.c.user_id == user_id, operate_permissions.c.item_type == 3, operate_permissions.c.item_id == note_id)
    result = await db.execute(query)
    relation = result.first()
    if relation:
        raise HTTPException(status_code=403, detail="You have no permission to edit")
    # 查询必要信息
    query = select(Note).where(Note.id == note_id)                                          
    result = await db.execute(query)
    note = result.scalar_one_or_none()
    query = select(Article.name, Article.folder_id, Article.group_id).where(Article.id == note.article_id)    # 所属文献名
    result = await db.execute(query)
    article_info = result.one_or_none()
    article_name, folder_id, group_id = article_info
    query = select(Folder.name).where(Folder.id == folder_id)                               # 所属文件夹名
    result = await db.execute(query)
    folder_name = result.scalar_one_or_none()
    # 修改并写日志
    if note_title:
        new_log = insert(group_logs).values(group_id=group_id, type=13, person1=user_id, folder=folder_name, article=article_name, note=note.title, note_new=note_title)
        await db.execute(new_log)
        note.title = note_title 
    if note_content:
        new_log = insert(group_logs).values(group_id=group_id, type=14, person1=user_id, folder=folder_name, article=article_name, note=note.title, note_content=note.content, note_new=note_content)
        await db.execute(new_log)
        note.content = note_content
    await db.commit()
    await db.refresh(note)

async def crud_read_note(note_id: int, db: AsyncSession):
    query = select(Note).where(Note.id == note_id)
    result = await db.execute(query)
    note = result.scalar_one_or_none()
    return note.content, note.update_time

async def crud_logs(group_id: int, page_number: int, page_size: int, db: AsyncSession):
    # 查询log总条数和对应页的log
    query = select(group_logs).where(group_logs.c.group_id == group_id)
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total_num = count_result.scalar()
    result = await db.execute(query)
    logs = result.fetchall()
    # 反序和分页
    logs = logs[::-1]
    logs = logs[(page_number - 1) * page_size : page_number * page_size] if page_number and page_size else logs
    # 处理18种情况
    return_value = []
    for log in logs:
        if log.type == 0 or log.type == 1 or log.type == 2 or log.type == 6:
            person1 = await get_username_by_id(log.person1, db)
            return_value.append({"type": log.type, "person1": person1, "time": log.time})
            continue
        if log.type == 3 or log.type == 4:
            person2 = await get_username_by_id(log.person2, db)
            return_value.append({"type": log.type, "person2": person2, "time": log.time})
            continue
        if log.type == 5:
            person1 = await get_username_by_id(log.person1, db)
            person2 = await get_username_by_id(log.person2, db)
            return_value.append({"type": log.type, "person1": person1, "person2": person2, "time": log.time})
            continue
        if log.type == 7:
            person1 = await get_username_by_id(log.person1, db)
            return_value.append({"type": log.type, "person1": person1, "folder": log.folder, "time": log.time})
            continue
        if log.type == 8:
            person1 = await get_username_by_id(log.person1, db)
            return_value.append({"type": log.type, "person1": person1, "folder": log.folder, "article": log.article, "time": log.time})
            continue
        if log.type == 9:
            person1 = await get_username_by_id(log.person1, db)
            return_value.append({"type": log.type, "person1": person1, "folder": log.folder, "article": log.article, "note": log.note, "time": log.time})
            continue
        if log.type == 10:
            person1 = await get_username_by_id(log.person1, db)
            return_value.append({"type": log.type, "person1": person1, "folder": log.folder, "folder_new": log.folder_new, "time": log.time})
            continue
        if log.type == 11:
            person1 = await get_username_by_id(log.person1, db)
            return_value.append({"type": log.type, "person1": person1, "folder": log.folder, "article": log.article, "article_new": log.article_new, "time": log.time})
            continue
        if log.type == 12:
            person1 = await get_username_by_id(log.person1, db)
            return_value.append({"type": log.type, "person1": person1, "folder": log.folder, "article": log.article, "article_tags": log.article_tags, "article_new": log.article_new, "time": log.time})
            continue
        if log.type == 13:
            person1 = await get_username_by_id(log.person1, db)
            return_value.append({"type": log.type, "person1": person1, "folder": log.folder, "article": log.article, "note": log.note, "note_new": log.note_new, "time": log.time})
            continue
        if log.type == 14:
            person1 = await get_username_by_id(log.person1, db)
            return_value.append({"type": log.type, "person1": person1, "folder": log.folder, "article": log.article, "note": log.note, "note_content": log.note_content, "note_new": log.note_new, "time": log.time})
            continue
        if log.type == 15:
            person1 = await get_username_by_id(log.person1, db)
            return_value.append({"type": log.type, "person1": person1, "folder": log.folder, "time": log.time})
            continue
        if log.type == 16:
            person1 = await get_username_by_id(log.person1, db)
            return_value.append({"type": log.type, "person1": person1, "folder": log.folder, "article": log.article, "time": log.time})
            continue
        if log.type == 17:
            person1 = await get_username_by_id(log.person1, db)
            return_value.append({"type": log.type, "person1": person1, "folder": log.folder, "article": log.article, "note": log.note, "time": log.time})
            continue
    return total_num, return_value

async def get_username_by_id(user_id: int, db: AsyncSession):
    query = select(User.username).where(User.id == user_id)
    result = await db.execute(query)
    username = result.scalar_one_or_none()
    return username

async def crud_disband(group_id: int, user_id: int, db: AsyncSession):
    # 非组织 leader 不得解散组织
    query = select(Group.leader).where(Group.id == group_id)
    result = await db.execute(query)
    leader_id = result.scalar_one_or_none()
    if user_id != leader_id:
        raise HTTPException(status_code=405, detail="Only leader can disband the group")
    # 找到该组织的所有文献
    query = select(Article.url).where(Article.group_id == group_id)
    result = await db.execute(query)
    article_urls = result.scalars().all()
    # 找到该组织的头像
    query = select(Group.avatar).where(Group.id == group_id)
    result = await db.execute(query)
    avatar_url = result.scalar_one_or_none()
    # 解散组织
    query = delete(Group).where(Group.id == group_id)
    result = await db.execute(query)
    await db.commit()

    return article_urls, avatar_url