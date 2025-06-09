from datetime import datetime
from pydantic import BaseModel

class NoteCreate(BaseModel):
    article_id: int
    content: str
    title: str

class NoteDelete(BaseModel):
    id: int

class NoteUpdate(BaseModel):
    id: int
    content: str | None = None
    title: str | None = None

class NoteFind(BaseModel):
    id: int | None = None
    article_id: int | None = None
    page: int | None = None
    page_size: int | None = None
    query: str | None = None

class NoteResponse(BaseModel):
    id: int
    title: str
    content: str
    article_id: int
    create_time: datetime 
    update_time: datetime 

    class Config:
        from_attributes = True