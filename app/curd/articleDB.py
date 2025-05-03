from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from app.models.model import ArticleDB
from app.schemas.articleDB import UploadArticle, GetArticle, DeLArticle, GetResponse

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
        total_count = 1
        articles = [articles] if articles else []
    elif get_article.page and get_article.page_size:
        count_result = await db.execute(select(func.count()).select_from(UploadArticle))
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
    
async def get_article_in_db_by_id(db: AsyncSession, article_id: int):
    """
    Get an article by its ID.
    """
    result = await db.execute(select(ArticleDB).where(ArticleDB.id == article_id))
    article = result.scalars().first()
    return article