from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from app.models.model import ArticleDB
from app.schemas.articleDB import UploadArticle, GetArticle, DeLArticle, GetResponse, SearchArticle, RecommendArticle

async def create_article_in_db(db: AsyncSession, upload_article: UploadArticle):
    """
    Create a new article in the database.
    """
    article =ArticleDB(title=upload_article.title, url=upload_article.url, author=upload_article.author, file_path=upload_article.file_path)
    db.add(article)
    await db.commit()
    await db.refresh(article)
    return article

async def get_article_in_db(db: AsyncSession, get_article: GetArticle):

    if get_article.id:
        result = await db.execute(select(ArticleDB).where(ArticleDB.id == get_article.id))
        articles = result.scalars().first()
        if not articles:
            return [], 0
        articles.clicks += 1  # 增加点击量
        await db.commit()
        await db.refresh(articles)  # 刷新以获取最新数据
        total_count = 1
        articles = [articles] if articles else []
    elif get_article.page and get_article.page_size:
        count_result = await db.execute(select(func.count()).select_from(ArticleDB))
        total_count = count_result.scalar()  # 获取总数
        # 分页查询文章
        result = await db.execute(
            select(ArticleDB)
            .offset((get_article.page - 1) * get_article.page_size)
            .limit(get_article.page_size)
        )
        articles = result.scalars().all()
    else:
        result = await db.execute(select(ArticleDB))
        articles = result.scalars().all()
        total_count = len(articles)
        
    return [GetResponse.model_validate(article) for article in articles], total_count

async def search_article_in_db(db: AsyncSession, search_article: SearchArticle):
    """
    Search for articles by title.
    """
    if search_article.author:
        result = await db.execute(select(ArticleDB).where(ArticleDB.title.like(f"%{search_article.query}%"), ArticleDB.author.like(f"%{search_article.author}%")))
        articles = result.scalars().all()
        total_count = len(articles)
    elif search_article.page and search_article.page_size:
        count_result = await db.execute(select(func.count()).select_from(ArticleDB).where(ArticleDB.title.like(f"%{search_article.query}%")))
        total_count = count_result.scalar()
        # 分页查询文章
        result = await db.execute(
            select(ArticleDB)
            .where(ArticleDB.title.like(f"%{search_article.query}%"))
            .offset((search_article.page - 1) * search_article.page_size)
            .limit(search_article.page_size)
        )
        articles = result.scalars().all()
    else:
        result = await db.execute(select(ArticleDB).where(ArticleDB.title.like(f"%{search_article.query}%")))
        articles = result.scalars().all()
        total_count = len(articles)
    # 更新所有搜索到文章的点击量
    return [GetResponse.model_validate(article) for article in articles], total_count
    
async def get_article_in_db_by_id(db: AsyncSession, article_id: int):
    """
    Get an article by its ID.
    """
    result = await db.execute(select(ArticleDB).where(ArticleDB.id == article_id))
    article = result.scalars().first()
    return article

async def get_article_info_in_db_by_id(db: AsyncSession, article_id: int):
    """
    Get an article by its ID.
    """
    result = await db.execute(select(ArticleDB).where(ArticleDB.id == article_id))
    article = result.scalars().first()
    if not article:
        return None, None
    return article.file_path, article.title

async def recommend_article_in_db(db: AsyncSession, recommend_article: RecommendArticle):
    """
    Recommend articles based on the number of clicks.
    """
    size = recommend_article.size or 10 
    result = await db.execute(
        select(ArticleDB).order_by(ArticleDB.clicks.desc())
        .limit(size)
    )
    articles = result.scalars().all()

    return [GetResponse.model_validate(article) for article in articles]

async def update_article_intro(db: AsyncSession, article_id: int, intro: str):
    """
    Update the introduction of an article.
    """
    result = await db.execute(select(ArticleDB).where(ArticleDB.id == article_id))
    article = result.scalars().first()
    
    if not article:
        return None
    
    article.intro = intro
    await db.commit()
    await db.refresh(article)
    
    return GetResponse.model_validate(article)