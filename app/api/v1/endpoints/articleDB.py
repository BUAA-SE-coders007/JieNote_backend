from fastapi import APIRouter, HTTPException, Depends, UploadFile, Form, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.get_db import get_db
from app.schemas.articleDB import UploadArticle, GetArticle, DeLArticle, GetResponse, SearchArticle, RecommendArticle
from app.curd.articleDB import  create_article_in_db, get_article_in_db, get_article_in_db_by_id, get_article_info_in_db_by_id, search_article_in_db, recommend_article_in_db
from app.core.config import settings
import os
import uuid
from fastapi.responses import FileResponse
from urllib.parse import quote
from app.curd.article import crud_upload_to_self_folder
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
    
@router.get("/get", response_model=dict)
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


@router.get("/search", response_model=dict)
async def search_article(search_article: SearchArticle = Depends(), db: AsyncSession = Depends(get_db)):
    """
    Search for an article by title.
    """
    # 根据标题查询文章信息
    articles, total_count = await search_article_in_db(db=db, search_article=search_article)
    return {
        "pagination": {
            "page": search_article.page,
            "page_size": search_article.page_size,
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
from app.utils.auth import get_current_user
@router.put("/copy", response_model=dict)
async def copy_article(folder_id: int, article_id: int, is_group: bool | None = None, db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    """
    Copy an article file by its ID to a specified directory.
    """
    # 根据 ID 查询文章信息
    file_path, title = await get_article_info_in_db_by_id(db=db, article_id=article_id)
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")
    old_file_path = file_path
    
    if is_group != None and is_group is True:
        url = f"/lhcos-data/{uuid.uuid4()}.pdf"
        with open(old_file_path, "rb") as source_file:
            with open(url, "wb") as dest_file:
                dest_file.write(source_file.read())
        # 用文件名（不带扩展名）作为 Article 名称
        user_id = user.get("id")
        from app.curd.group import crud_new_article
        article_id = await crud_new_article(user_id, folder_id, title, url, db)  
        return {"msg": "Article copied successfully", "new_article_id": article_id}

    new_article_id = await crud_upload_to_self_folder(name=title, folder_id=folder_id, url=old_file_path ,db=db)
    
    # 复制文件到新的目录
    new_file_path = os.path.join("/lhcos-data", f"{new_article_id}.pdf")
    try:
        with open(old_file_path, "rb") as source_file:
            with open(new_file_path, "wb") as dest_file:
                dest_file.write(source_file.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"msg": "Article copied successfully", "new_article_id": new_article_id}

@router.get("/recommend", response_model=dict)
async def recommend_article(recommend_article: RecommendArticle = Depends(), db: AsyncSession = Depends(get_db)):
    articles = await recommend_article_in_db(db=db, recommend_article=recommend_article)
    return {
        "pagination": {
            "total_count": recommend_article.size,
        },
        "articles": [articles.model_dump() for articles in articles]
    }


