from pydantic import BaseModel

class ApplyToEnter(BaseModel):
    group_id: int

class LeaveGroup(BaseModel):
    group_id: int