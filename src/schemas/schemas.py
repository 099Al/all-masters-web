from pydantic import BaseModel

class UserMessageCreate(BaseModel):
    user_id: int        # от кого
    specialist_id: int  # кому
    message: str
