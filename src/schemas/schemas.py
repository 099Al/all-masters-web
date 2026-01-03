from datetime import datetime

from pydantic import BaseModel

class MessagesListIn(BaseModel):
    specialist_id: int


class MessageCreate(BaseModel):
    # user_id: int        # от кого
    specialist_id: int  # кому
    message: str


class MessageUpdate(BaseModel):
    message: str

class MessageOut(BaseModel):
    id: int
    user_id: int
    specialist_id: int
    message: str
    created_at: datetime | None = None

class MessagesQuery(BaseModel):
    user_id: int
    specialist_id: int

