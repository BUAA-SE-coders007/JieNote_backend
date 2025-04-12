from pydantic import BaseModel

class NoteCreate(BaseModel):
    article_id: int
    content: str

class NoteDelete(BaseModel):
    id: int

class NoteUpdate(BaseModel):
    id: int
    content: str

