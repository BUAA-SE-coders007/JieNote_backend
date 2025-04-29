from fastapi import APIRouter, HTTPException, Depends, UploadFile, Form, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.get_db import get_db
from app.schemas.articleDB import UploadArticle, GetArticle, DeLArticle, GetResponse
from app.curd.articleDB import  create_article_in_db, get_article_in_db, get_article_in_db_by_id
from app.core.config import settings
import os
import uuid
from fastapi.responses import FileResponse
from urllib.parse import quote
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
    # 将文件保存到指定目录
    if not os.path.exists(settings.UPLOAD_FOLDER):
        os.makedirs(settings.UPLOAD_FOLDER)

    # 生成文件名,可以使用 UUID 或者其他方式来确保文件名唯一
    file_name = f"{uuid.uuid4()}.pdf"
    file_path = os.path.join(settings.UPLOAD_FOLDER, file_name)
    try:
        with open(file_path, "wb") as f:
            while chunk := await file.read(1024):  # 每次读取 1024 字节
                f.write(chunk)
        
        await create_article_in_db(db=db, upload_article=UploadArticle(title=title, author=author, url=url, file_path=file_path))
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

@router.get("/download/{article_id}", response_model=dict)
async def download_article(article_id: int, db: AsyncSession = Depends(get_db)):
    """
    Download an article file by its ID.
    """
    # 根据 ID 查询文章信息
    article = await get_article_in_db_by_id(db=db, article_id=article_id)
    if not article or not article.file_path:
        raise HTTPException(status_code=404, detail="File not found")

    if not os.path.exists(article.file_path):
        raise HTTPException(status_code=404, detail="File not found on server")
    
    # 从文件路径获取文件名
    file_name = os.path.basename(article.file_path)
    
    # 设置原始文件名，如果有标题，使用标题作为文件名
    download_filename = f"{article.title}.pdf" if article.title else file_name
    
    # 返回文件，并设置文件名（使用 quote 处理中文文件名）
    return FileResponse(
        path=article.file_path,
        filename=quote(download_filename),
        media_type="application/pdf"
    )