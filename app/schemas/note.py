from datetime import datetime
from pydantic import BaseModel

class NoteCreate(BaseModel):
    article_id: int
    content: str

class NoteDelete(BaseModel):
    id: int

class NoteUpdate(BaseModel):
    id: int
    content: str

class NoteFind(BaseModel):
    id: int | None = None
    article_id: int | None = None
    page: int | None = None
    page_size: int | None = None

class NoteResponse(BaseModel):
    id: int
    content: str
    article_id: int
    create_time: datetime 
    update_time: datetime 

    class Config:
        from_attributes = True