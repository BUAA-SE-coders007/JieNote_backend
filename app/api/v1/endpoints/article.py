from fastapi import APIRouter, UploadFile, File, Query, Depends, HTTPException, Body
from fastapi.responses import FileResponse
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import os
import io
from zipfile import ZipFile
import zipfile
import tempfile

from app.utils.get_db import get_db
from app.utils.auth import get_current_user
from app.curd.article import crud_upload_to_self_folder, crud_get_self_folders, crud_get_articles_in_folder, crud_self_create_folder, crud_self_article_to_recycle_bin, crud_self_folder_to_recycle_bin, crud_read_article, crud_import_self_folder, crud_export_self_folder,crud_create_tag, crud_delete_tag, crud_get_article_tags, crud_all_tags_order, crud_change_folder_name, crud_change_article_name, crud_article_statistic
from app.schemas.article import SelfCreateFolder

router = APIRouter()

@router.post("/uploadToSelfFolder", response_model="dict")
async def upload_to_self_folder(folder_id: int = Query(...), article: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    # 由前端保证上传的为 PDF
    # 用文件名（不带扩展名）作为 Article 名称
    name = os.path.splitext(article.filename)[0]

    # 新建 Article 记录
    article_id = await crud_upload_to_self_folder(name, folder_id, db)

    # 存储到云存储位置
    os.makedirs("/lhcos-data", exist_ok=True)
    save_path = os.path.join("/lhcos-data", f"{article_id}.pdf")
    with open(save_path, "wb") as f:
        content = await article.read()
        f.write(content)

    return {"msg": "Article created successfully."}

@router.get("/getSelfFolders", response_model="dict")
async def get_self_folders(page_number: Optional[int] = Query(None, ge=1), page_size: Optional[int] = Query(None, ge=1), 
                     db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    # 获取用户id
    user_id = user.get("id")

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
async def self_create_folder(model: SelfCreateFolder, db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    folder_name = model.folder_name
    if folder_name == "" or len(folder_name) > 30:
        raise HTTPException(status_code=405, detail="Invalid folder name, empty or longer than 30")
    
    # 获取用户id
    user_id = user.get("id")

    # 数据库插入
    await crud_self_create_folder(folder_name, user_id, db)

    # 返回结果
    return {"msg": "User Folder Created Successfully"}

@router.delete("/selfArticleToRecycleBin", response_model="dict")
async def self_article_to_recycle_bin(article_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    await crud_self_article_to_recycle_bin(article_id, db)
    return {"msg": "Article is moved to recycle bin"}

@router.delete("/selfFolderToRecycleBin", response_model="dict")
async def self_folder_to_recycle_bin(folder_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    await crud_self_folder_to_recycle_bin(folder_id, db)
    return {"msg": "Folder is moved to recycle bin"}

@router.post("/annotateSelfArticle", response_model="dict")
async def annotate_self_article(article_id: int = Query(...), article: UploadFile = File(...)):
    # 将新文件存储到云存储位置
    save_path = os.path.join("/lhcos-data", f"{article_id}.pdf")
    with open(save_path, "wb") as f:
        content = await article.read()
        f.write(content)

    return {"msg": "Article annotated successfully."}

@router.get("/readArticle", response_class=FileResponse)
async def read_article(article_id: int = Query(...), db: AsyncSession = Depends(get_db)):

    file_path = f"/lhcos-data/{article_id}.pdf"

    # 查询文件名
    article_name = await crud_read_article(article_id, db)

    # 返回结果
    return FileResponse(path=file_path, filename=f"{article_name}.pdf", media_type='application/pdf')

@router.post("/importSelfFolder", response_model="dict")
async def import_self_folder(folder_name: str = Query(...), zip: UploadFile = File(...), db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    if folder_name == "" or len(folder_name) > 30:
        raise HTTPException(status_code=405, detail="Invalid folder name, empty or longer than 30")
    
    # 获取用户id
    user_id = user.get("id")

    # 获取压缩包中的所有文献名(去掉.pdf)
    zip_bytes = await zip.read()
    zip_file = ZipFile(io.BytesIO(zip_bytes))
    article_names = [os.path.splitext(os.path.basename(name))[0] for name in zip_file.namelist() if name.endswith('.pdf')]

    # 记入数据库
    result = await crud_import_self_folder(folder_name, article_names, user_id, db)

    # 存储文献到云存储
    for i in range(0, len(result), 2):
        article_id = result[i]
        article_name = result[i + 1]
        pdf_filename_in_zip = f"{article_name}.pdf"
        with zip_file.open(pdf_filename_in_zip) as source_file:
            target_path = os.path.join("/lhcos-data", f"{article_id}.pdf")
            with open(target_path, "wb") as out_file:
                out_file.write(source_file.read())

    return {"msg": "Successfully import articles"}

@router.get("/exportSelfFolder", response_class=FileResponse)
async def export_self_folder(background_tasks: BackgroundTasks, folder_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    zip_name, article_ids, article_names = await crud_export_self_folder(folder_id, db)
            
    tmp_dir = tempfile.gettempdir()
    zip_path = os.path.join(tmp_dir, f"{zip_name}.zip")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for article_id, article_name in zip(article_ids, article_names):
            pdf_path = os.path.join("/lhcos-data", f"{article_id}.pdf")
            arcname = f"{article_name}.pdf"  # 压缩包内的文件名
            zipf.write(pdf_path, arcname=arcname)

    background_tasks.add_task(os.remove, zip_path)

    return FileResponse(
        path=zip_path,
        filename=f"{zip_name}.zip",
        media_type="application/zip"
    )

@router.post("/createTag", response_model="dict")
async def create_tag(article_id: int = Body(...), content: str = Body(...), db: AsyncSession = Depends(get_db)):
    if len(content) > 30:
        raise HTTPException(status_code=405, detail="Invalid tag content, longer than 30")
    await crud_create_tag(article_id, content, db)
    return {"msg": "Tag Created Successfully"}

@router.delete("/deleteTag", response_model="dict")
async def delete_tag(tag_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    await crud_delete_tag(tag_id, db)
    return {"msg": "Tag deleted successfully"}

@router.get("/getArticleTags", response_model="dict")
async def get_article_tags(article_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    tags = await crud_get_article_tags(article_id, db)
    result = [{"tag_id": tag.id, "tag_content": tag.content} for tag in tags]
    return {"result": result}

@router.post("/allTagsOrder", response_model="dict")
async def all_tags_order(article_id: int = Body(...), tag_contents: List[str] = Body(...), db: AsyncSession = Depends(get_db)):
    for tag_content in tag_contents:
        if len(tag_content) > 30:
            raise HTTPException(status_code=405, detail="Invalid tag content existed, longer than 30")
    await crud_all_tags_order(article_id, tag_contents, db)
    return {"msg": "Tags and order changed successfully"}

@router.post("/changeFolderName", response_model="dict")
async def change_folder_name(folder_id: int = Body(...), folder_name: str = Body(...), db: AsyncSession = Depends(get_db)):
    if folder_name == "" or len(folder_name) > 30:
        raise HTTPException(status_code=405, detail="Invalid folder name, empty or longer than 30")
    await crud_change_folder_name(folder_id, folder_name, db)
    return {"msg": "Folder name changed successfully"}

@router.post("/changeArticleName", response_model="dict")
async def change_article_name(article_id: int = Body(...), article_name: str = Body(...), db: AsyncSession = Depends(get_db)):
    await crud_change_article_name(article_id, article_name, db)
    return {"msg": "Article name changed successfully"}