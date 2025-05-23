from pydantic import BaseModel

class LeaveGroup(BaseModel):
    group_id: int

class EnterGroup(BaseModel):
    inviteCode: str