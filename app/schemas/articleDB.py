from pydantic import BaseModel
from datetime import datetime

class UploadArticle(BaseModel):
    title: str
    author: str
    url: str
    file_path: str

class GetArticle(BaseModel):
    id: int | None = None
    page: int | None = None
    page_size: int | None = None

class SearchArticle(BaseModel):
    query: str
    author: str | None = None
    page: int | None = None
    page_size: int | None = None

class DeLArticle(BaseModel):
    id: int

class GetResponse(BaseModel):
    id: int
    title: str
    url: str
    create_time: datetime 
    update_time: datetime 
    author: str
    file_path: str

    class Config:
        from_attributes = True