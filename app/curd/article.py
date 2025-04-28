from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy import func, cast, Date
from datetime import datetime, timedelta
from app.models.model import User, Group, Folder, Article, Note, Tag, user_group

async def crud_upload_to_self_folder(name: str, folder_id: int, db: AsyncSession):
    new_article = Article(name=name, folder_id=folder_id)
    db.add(new_article)
    await db.commit()
    await db.refresh(new_article)
    return new_article.id

async def crud_get_self_folders(user_id: int, page_number: int, page_size: int, db: AsyncSession):
    query = select(Folder).where(Folder.user_id == user_id, Folder.visible == True).order_by(Folder.id.desc())
    if page_number and page_size:
        offset = (page_number - 1) * page_size
        query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    folders = result.scalars().all()
    return folders

async def crud_get_articles_in_folder(folder_id: int, page_number: int, page_size: int, db: AsyncSession):
    query = select(Article).where(Article.folder_id == folder_id, Article.visible == True).order_by(Article.id.desc())
    if page_number and page_size:
        offset = (page_number - 1) * page_size
        query = query.offset(offset).limit(page_size)
    
    result = await db.execute(query)
    articles = result.scalars().all()
    return articles

async def crud_self_create_folder(name: str, user_id: int, db: AsyncSession):
    new_folder = Folder(name=name, user_id=user_id)
    db.add(new_folder)
    await db.commit()
    await db.refresh(new_folder)

async def crud_self_article_to_recycle_bin(article_id: int, db: AsyncSession):
    # 查询 article
    query = select(Article).where(Article.id == article_id)
    result = await db.execute(query)
    article = result.scalar_one_or_none()

    # 修改 visible 字段
    article.visible = False
    await db.commit()
    await db.refresh(article)

async def crud_self_folder_to_recycle_bin(folder_id: int,  db: AsyncSession):
    # 查询 folder
    query = select(Folder).where(Folder.id == folder_id)
    result = await db.execute(query)
    folder = result.scalar_one_or_none()

    # 修改 visible 字段
    folder.visible = False
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
    print(tomorrow)
    print(seven_days_ago)

    # 查询近7天内的笔记数目，按日期分组
    query = (
        select(
            cast(Article.create_time, Date).label("date"),  # 按日期分组
            func.count(Article.id).label("count")           # 统计每日期的笔记数
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