from pydantic import BaseModel

class NoteInput(BaseModel):
    input: str