from fastapi import APIRouter, HTTPException, Depends, UploadFile, Form, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.get_db import get_db
from app.schemas.articleDB import UploadArticle, GetArticle, DeLArticle, GetResponse
from app.curd.articleDB import  create_article_in_db, get_article_in_db

router = APIRouter()

@router.put("/upload", response_model=dict)
async def upload_article(
    title: str = Form(None),
    author: str = Form(None),
    url: str = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload an article to the database.
    """
    try:
        await create_article_in_db(db=db, upload_article=UploadArticle(title=title, author=author, url=url))
        return {"msg": "Article uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("", response_model=dict)
async def get_article(get_article: GetArticle = Depends(), db: AsyncSession = Depends(get_db)):
    """
    Get an article from the database.
    """
    articles, total_count = await get_article_in_db(db=db, get_article=get_article)
    return {
        "pagination": {
            "page": get_article.page,
            "page_size": get_article.page_size,
            "total_count": total_count
        },
        "articles": [articles.model_dump() for articles in articles]
    }