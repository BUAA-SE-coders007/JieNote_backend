from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select
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

async def crud_self_article_to_recycle_bin(article_id: int, user_id: int, db: AsyncSession):
    # 1. 异步查询 article，并加载 folder 关系
    query = select(Article).options(selectinload(Article.folder)).where(Article.id == article_id)
    result = await db.execute(query)
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article Not Found")

    # 2. 检查是否是自己个人的article
    if article.folder.user_id != user_id:
        raise HTTPException(status_code=403, detail="This is not your own article")

    # 3. 修改 visible 字段
    article.visible = False
    await db.commit()
    await db.refresh(article)

async def crud_self_folder_to_recycle_bin(folder_id: int, user_id: int, db: AsyncSession):
    # 1. 异步查询 folder
    query = select(Folder).where(Folder.id == folder_id)
    result = await db.execute(query)
    folder = result.scalar_one_or_none()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder Not Found")
    
    # 2. 检查是否是自己个人的folder
    if folder.user_id != user_id:
        raise HTTPException(status_code=403, detail="This is not your own folder")
    
    # 3. 修改 visible 字段
    folder.visible = False
    await db.commit()
    await db.refresh(folder)

async def crud_read_article(article_id: int, db: AsyncSession):
    query = select(Article).where(Article.id == article_id)
    result = await db.execute(query)
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article.name

async def crud_import_self_folder(folder_name: str, article_names, user_id: int, db: AsyncSession):
    result = []

    # 新建文件夹
    new_folder = Folder(name=folder_name, user_id=user_id)
    db.add(new_folder)
    await db.commit()
    await db.refresh(new_folder)

    # 新建文献
    for article_name in article_names:
        new_article = Article(name=article_name, folder_id=new_folder.id)
        db.add(new_article)
        await db.commit()
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