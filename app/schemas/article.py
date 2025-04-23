from pydantic import BaseModel

class SelfCreateFolder(BaseModel):
    folder_name: str