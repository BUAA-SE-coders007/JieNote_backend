from fastapi import APIRouter, UploadFile, File, Query, Depends, HTTPException, Body
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import os

from utils.get_db import get_db
from utils.auth import get_current_user
from curd.user import get_user_by_email
from curd.article import crud_upload_to_self_folder, crud_get_self_folders, crud_get_articles_in_folder, crud_self_create_folder, crud_self_article_to_recycle_bin, crud_self_folder_to_recycle_bin, crud_read_article

router = APIRouter()

@router.post("/uploadToSelfFolder", response_model="dict")
async def upload_to_self_folder(folder_id: int = Query(...), article: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    # 检查是否为 PDF 文件
    if article.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    # 用文件名（不带扩展名）作为 Article 名称
    name = os.path.splitext(article.filename)[0]

    # 新建 Article 记录
    article_id = await crud_upload_to_self_folder(name, folder_id, db)

    # 存储文件，暂时存储到本地
    save_dir = "articles"
    os.makedirs(save_dir, exist_ok=True)  # 如果目录不存在则创建
    save_path = os.path.join(save_dir, f"{article_id}.pdf")
    with open(save_path, "wb") as f:
        content = await article.read()
        f.write(content)

    return {"msg": "Article created successfully."}

@router.get("/getSelfFolders", response_model="dict")
async def get_self_folders(page_number: Optional[int] = Query(None, ge=1), page_size: Optional[int] = Query(None, ge=1), 
                     db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    # 获取用户邮箱
    user_email = user.get("email")
    if not user_email:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # 由邮箱查得id
    db_user = await get_user_by_email(db, user_email)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    user_id = db_user.id

    # 数据库查询
    folders = await crud_get_self_folders(user_id, page_number, page_size, db)

    # 返回结果
    result = [{"folder_id": folder.id, "folder_name": folder.name} for folder in folders]
    return {"result": result}

@router.get("/getArticlesInFolder", response_model="dict")
async def get_articles_in_folder(folder_id: int = Query(...), page_number: Optional[int] = Query(None, ge=1), page_size: Optional[int] = Query(None, ge=1), 
                     db: AsyncSession = Depends(get_db)):
    articles = await crud_get_articles_in_folder(folder_id, page_number, page_size, db)
    result = [{"article_id": article.id, "article_name": article.name} for article in articles]
    return {"result": result}

@router.post("/selfCreateFolder", response_model="dict")
async def self_create_folder(folder_name: str = Body(...), db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    if folder_name == "":
        raise HTTPException(status_code=405, detail="Empty Folder Name")
    
    # 获取用户邮箱
    user_email = user.get("email")
    if not user_email:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # 由邮箱查得id
    db_user = await get_user_by_email(db, user_email)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    user_id = db_user.id

    # 数据库插入
    await crud_self_create_folder(folder_name, user_id, db)

    # 返回结果
    return {"msg": "User Folder Created Successfully"}

@router.delete("/selfArticleToRecycleBin", resplonse_model="dict")
async def self_article_to_recycle_bin(article_id: int = Query(...), db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    # 获取用户邮箱
    user_email = user.get("email")
    if not user_email:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # 由邮箱查得id
    db_user = await get_user_by_email(db, user_email)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    user_id = db_user.id

    # 数据库修改
    await crud_self_article_to_recycle_bin(article_id, user_id, db)

    # 返回结果
    return {"msg": "Article is moved to recycle bin"}

@router.delete("/selfFolderToRecycleBin", response_model="dict")
async def self_folder_to_recycle_bin(folder_id: int = Query(...), db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    # 获取用户邮箱
    user_email = user.get("email")
    if not user_email:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # 由邮箱查得id
    db_user = await get_user_by_email(db, user_email)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    user_id = db_user.id

    # 数据库修改
    await crud_self_folder_to_recycle_bin(folder_id, user_id, db)

    # 返回结果
    return {"msg": "Folder is moved to recycle bin"}

@router.post("/annotateSelfArticle", response_model="dict")
async def annotate_self_article(article_id: int = Query(...), article: UploadFile = File(...)):
    # 存储文件，将新文件暂时存储到本地
    save_dir = "articles"
    os.makedirs(save_dir, exist_ok=True)  # 如果目录不存在则创建
    save_path = os.path.join(save_dir, f"{article_id}.pdf")
    with open(save_path, "wb") as f:
        content = await article.read()
        f.write(content)

    return {"msg": "Article annotated successfully."}

@router.get("/readArticle", response_class=FileResponse)
async def read_article(article_id: int = Query(...), db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    # 获取用户邮箱
    user_email = user.get("email")
    if not user_email:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # 由邮箱查得id
    db_user = await get_user_by_email(db, user_email)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    user_id = db_user.id

    # 文件路径
    file_path = f"articles/{article_id}.pdf"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="PDF file not found")
    
    # 查询文件名
    article_name = await crud_read_article(article_id, user_id, db)

    # 返回结果
    return FileResponse(path=file_path, filename=f"{article_name}.pdf", media_type='application/pdf')