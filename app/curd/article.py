from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, insert, desc
from sqlalchemy import func, cast, Date
from datetime import datetime, timedelta
from app.models.model import User, Group, Folder, Article, Note, Tag, user_group, self_recycle_bin

async def crud_upload_to_self_folder(name: str, folder_id: int, db: AsyncSession):
    new_article = Article(name=name, folder_id=folder_id)
    db.add(new_article)
    await db.commit()
    await db.refresh(new_article)
    return new_article.id

async def crud_get_self_folders(user_id: int, page_number: int, page_size: int, db: AsyncSession):
    query = select(Folder).where(Folder.user_id == user_id, Folder.visible == True).order_by(Folder.id.desc())
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total_num = count_result.scalar()

    if page_number and page_size:
        offset = (page_number - 1) * page_size
        query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    folders = result.scalars().all()

    return total_num, folders

async def crud_get_articles_in_folder(folder_id: int, page_number: int, page_size: int, db: AsyncSession):
    query = select(Article).where(Article.folder_id == folder_id, Article.visible == True).order_by(Article.id.desc())
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total_num = count_result.scalar()

    if page_number and page_size:
        offset = (page_number - 1) * page_size
        query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    articles = result.scalars().all()

    return total_num, articles

async def crud_self_create_folder(name: str, user_id: int, db: AsyncSession):
    new_folder = Folder(name=name, user_id=user_id)
    db.add(new_folder)
    await db.commit()
    await db.refresh(new_folder)
    return new_folder.id

async def crud_self_article_to_recycle_bin(article_id: int, user_id: int, db: AsyncSession):
    # 维护 article 表
    query = select(Article).where(Article.id == article_id)
    result = await db.execute(query)
    article = result.scalar_one_or_none()
    article.visible = False
    
    # 维护 self_recycle_bin 表
    recycle = insert(self_recycle_bin).values(user_id=user_id, type=2, id=article_id, name=article.name, folder_id=article.folder_id)
    await db.execute(recycle)

    await db.commit()
    await db.refresh(article)

async def crud_self_folder_to_recycle_bin(folder_id: int, user_id: int, db: AsyncSession):
    # 维护 folder 表
    query = select(Folder).where(Folder.id == folder_id)
    result = await db.execute(query)
    folder = result.scalar_one_or_none()
    folder.visible = False

    # 维护 self_recycle_bin 表
    recycle = insert(self_recycle_bin).values(user_id=user_id, type=1, id=folder_id, name=folder.name)
    await db.execute(recycle)

    await db.commit()
    await db.refresh(folder)

async def crud_read_article(article_id: int, db: AsyncSession):
    query = select(Article).where(Article.id == article_id)
    result = await db.execute(query)
    article = result.scalar_one_or_none()
    return article.name

async def crud_import_self_folder(folder_name: str, article_names, user_id: int, db: AsyncSession):
    result = []

    # 新建文件夹
    new_folder = Folder(name=folder_name, user_id=user_id)
    db.add(new_folder)
    await db.commit()
    await db.refresh(new_folder)

    # 新建文献
    new_articles = [Article(name=article_name, folder_id=new_folder.id) for article_name in article_names]
    db.add_all(new_articles)
    await db.commit()
    for new_article in new_articles:
        await db.refresh(new_article)
        result.append(new_article.id)
        result.append(new_article.name)
    
    return result

async def crud_export_self_folder(folder_id: int, db: AsyncSession):
    query = select(Folder).where(Folder.id == folder_id)
    result = await db.execute(query)
    folder = result.scalar_one_or_none()
    folder_name = folder.name

    query = select(Article).where(Article.folder_id == folder_id, Article.visible == True).order_by(Article.id.desc())
    result = await db.execute(query)
    articles = result.scalars().all()
    article_id = []
    article_name = []
    for article in articles:
        article_id.append(article.id)
        article_name.append(article.name)

    return folder_name, article_id, article_name

async def crud_create_tag(article_id: int, content: str, db: AsyncSession):
    new_tag = Tag(article_id=article_id, content=content)
    db.add(new_tag)
    await db.commit()
    await db.refresh(new_tag)

async def crud_delete_tag(tag_id: int, db: AsyncSession):
    query = select(Tag).filter(Tag.id == tag_id)
    result = await db.execute(query)
    tag = result.scalar_one_or_none()
    await db.delete(tag)
    await db.commit()

async def crud_get_article_tags(article_id: int, db: AsyncSession):
    query = select(Tag).where(Tag.article_id == article_id).order_by(Tag.id.asc())
    result = await db.execute(query)
    tags = result.scalars().all()
    return tags

async def crud_all_tags_order(article_id: int, tag_contents, db: AsyncSession):
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

async def crud_change_folder_name(folder_id: int, folder_name: str, db: AsyncSession):
    query = select(Folder).where(Folder.id == folder_id)
    result = await db.execute(query)
    folder = result.scalar_one_or_none()

    folder.name = folder_name
    await db.commit()
    await db.refresh(folder)

async def crud_change_article_name(article_id: int, article_name: str, db: AsyncSession):
    query = select(Article).where(Article.id == article_id)
    result = await db.execute(query)
    article = result.scalar_one_or_none()

    article.name = article_name
    await db.commit()
    await db.refresh(article)

async def crud_article_statistic(db: AsyncSession):
    # 获取明天日期和7天前的日期
    tomorrow = datetime.now().date() + timedelta(days=1)
    seven_days_ago = datetime.now().date() - timedelta(days=6)

    # 查询近7天内的文献数目，按日期分组
    query = (
        select(
            cast(Article.create_time, Date).label("date"),  # 按日期分组
            func.count(Article.id).label("count")           # 统计每日期的文献数
        )
        .where(
            Article.create_time >= seven_days_ago,          # 大于等于7天前的0点
            Article.create_time < tomorrow                  # 小于明天0点
        )
        .group_by(cast(Article.create_time, Date))          # 按日期分组
        .order_by(cast(Article.create_time, Date))          # 按日期排序
    )

    # 执行查询
    result = await db.execute(query)
    data = result.fetchall()

    # 格式化结果为字典列表
    articles = [{"date": row.date, "count": row.count} for row in data]

    # 若某日期没有记录，则为0
    for i in range(0, 7):
        if i == len(articles) or articles[i].get("date") != seven_days_ago + timedelta(days=i):
            articles.insert(i, {"date": seven_days_ago + timedelta(days=i), "count": 0})

    return articles

async def crud_self_tree(user_id: int, page_number: int, page_size: int, db: AsyncSession):
    query = select(Folder).where(Folder.user_id == user_id, Folder.visible == True).order_by(Folder.id.desc())
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
        query = select(Article).where(Article.folder_id == folder_array[i].get("folder_id"), Article.visible == True).order_by(Article.id.desc())
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
            query = select(Note).where(Note.article_id == article_array[j].get("article_id"), Note.visible == True).order_by(Note.id.desc())
            result = await db.execute(query)
            notes = result.scalars().all()
            note_array = [{"note_id": note.id, "note_title": note.title} for note in notes]
            article_array[j]["notes"] = note_array
    
    return total_num, folder_array

async def crud_self_article_statistic(user_id: int, db: AsyncSession):
    # 查询个人拥有的、未被删除的文献总数
    query = (
        select(func.count(Article.id))
        .join(Folder, Article.folder_id == Folder.id)
        .where(Folder.user_id == user_id, Folder.visible == True, Article.visible == True)
    )
    result = await db.execute(query)
    article_total_num = result.scalar_one_or_none()

    # 获取明天日期和7天前的日期
    tomorrow = datetime.now().date() + timedelta(days=1)
    seven_days_ago = datetime.now().date() - timedelta(days=6)

    # 查询近7天内的文献数目，按日期分组
    query = (
        select(
            cast(Article.create_time, Date).label("date"),  # 按日期分组
            func.count(Article.id).label("count")           # 统计每日期的文献数
        )
        .join(Folder, Article.folder_id == Folder.id)
        .where(
            Folder.user_id == user_id,
            Folder.visible == True,
            Article.visible == True,
            Article.create_time >= seven_days_ago,          # 大于等于7天前的0点
            Article.create_time < tomorrow,                 # 小于明天0点
        )
        .group_by(cast(Article.create_time, Date))          # 按日期分组
        .order_by(cast(Article.create_time, Date))          # 按日期排序
    )

    # 执行查询
    result = await db.execute(query)
    data = result.fetchall()

    # 格式化结果为字典列表
    articles = [{"date": row.date, "count": row.count} for row in data]

    # 若某日期没有记录，则为0
    for i in range(0, 7):
        if i == len(articles) or articles[i].get("date") != seven_days_ago + timedelta(days=i):
            articles.insert(i, {"date": seven_days_ago + timedelta(days=i), "count": 0})

    return article_total_num, articles

async def crud_items_in_recycle_bin(user_id: int, page_number: int, page_size: int, db: AsyncSession):
    query = select(
        self_recycle_bin.c.type,
        self_recycle_bin.c.id,
        self_recycle_bin.c.name,
        self_recycle_bin.c.create_time
    ).where(self_recycle_bin.c.user_id == user_id).order_by(desc(self_recycle_bin.c.create_time))

    if page_number and page_size:
        offset = (page_number - 1) * page_size
        query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    items = result.fetchall()

    return [{"type": item.type, "id": item.id, "name": item.name, "time": item.create_time.strftime("%Y-%m-%d %H:%M:%S")} for item in items]

async def crud_delete_forever(type: int, id: int, db: AsyncSession):
    query = delete(self_recycle_bin).where(self_recycle_bin.c.type == type, self_recycle_bin.c.id == id)
    await db.execute(query)
    if type == 1:
        query = delete(Folder).where(Folder.id==id)
    elif type == 2:
        query = delete(Article).where(Article.id==id)
    else:
        query = delete(Note).where(Note.id==id)
    await db.execute(query)
    await db.commit()

async def crud_recover(type: int, id: int, db: AsyncSession):
    query = select(self_recycle_bin).where(self_recycle_bin.c.type == type, self_recycle_bin.c.id == id)
    result = await db.execute(query)
    item = result.first()
    if type == 3:
        # 检查上级文献存在性
        query = select(Article).where(Article.id == item.article_id)
        result = await db.execute(query)
        article = result.scalar_one_or_none()
        article_name = article.name
        article_visible = article.visible
        # 检查上级文件夹存在性
        query = select(Folder).where(Folder.id == item.folder_id)
        result = await db.execute(query)
        folder = result.scalar_one_or_none()
        folder_name = folder.name
        folder_visible = folder.visible
        # 若上级不存在，则给用户以提示信息，请用户先恢复相应的文件夹和文献
        if not article_visible or not folder_visible:
            return {"info": "Note recovered failed, please check its upper-level node", "folder_name": folder_name, "article_name": article_name}
        # 若上级存在，则正常恢复即可，在回收站表中删除该表项，并将Note表中visible改为True
        query = delete(self_recycle_bin).where(self_recycle_bin.c.type == type, self_recycle_bin.c.id == id)
        await db.execute(query)
        query = select(Note).where(Note.id == id)
        result = await db.execute(query)
        note = result.scalar_one_or_none()
        note.visible = True
        await db.commit()
        await db.refresh(note)
        return {"info": "Note recovered successfully"}
    if type == 2:
        # 检查上级文件夹存在性
        query = select(Folder).where(Folder.id == item.folder_id)
        result = await db.execute(query)
        folder = result.scalar_one_or_none()
        folder_name = folder.name
        folder_visible = folder.visible
        # 若上级不存在，则给用户以提示信息，请用户先恢复相应的文件夹
        if not folder_visible:
            return {"info": "Article recovered failed, please check its upper-level node", "folder_name": folder_name}
        # 若上级存在，则正常恢复即可，在回收站表中删除该表项，并将Article表中visible改为True
        query = delete(self_recycle_bin).where(self_recycle_bin.c.type == type, self_recycle_bin.c.id == id)
        await db.execute(query)
        query = select(Article).where(Article.id == id)
        result = await db.execute(query)
        article = result.scalar_one_or_none()
        article.visible = True
        await db.commit()
        await db.refresh(article)
        return {"info": "Article recovered successfully"}
    if type == 1:
        # 正常恢复即可，在回收站表中删除该表项，并将Folder表中visible改为True
        query = delete(self_recycle_bin).where(self_recycle_bin.c.type == type, self_recycle_bin.c.id == id)
        await db.execute(query)
        query = select(Folder).where(Folder.id == id)
        result = await db.execute(query)
        folder = result.scalar_one_or_none()
        folder.visible = True
        await db.commit()
        await db.refresh(folder)
        return {"info": "Folder recovered successfully"}