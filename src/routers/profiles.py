import os
from datetime import datetime, timedelta

from urllib import request

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse

from fastapi.templating import Jinja2Templates
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session


from starlette.responses import FileResponse

from src.config_paramaters import UTC_PLUS_5, MESSAGES_TO_SPECIALISTS_LIMIT
from src.database.models import SpecialistPhotoType, models
from src.database.requests_web import ReqWeb
from src.database.connect import DataBase

import mimetypes

from src.schemas import schemas
from src.schemas.schemas import UserMessageCreate

router_profiles = APIRouter(
    prefix="/profiles",
    tags=["profile"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # текущая папка файла роутера
PROJECT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))  # поднимаемся в Project
AVATAR_DIR = os.path.join(PROJECT_DIR, "images", "avatars")

@router_profiles.get("/avatar/{filename}", name="get_avatar")
async def get_avatar(filename: str):
    file_path = os.path.join(AVATAR_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Avatar not found")
    mime_type, _ = mimetypes.guess_type(file_path)
    return FileResponse(file_path, media_type=mime_type or "application/octet-stream")
    #return FileResponse(file_path, media_type="image/jpeg")


templates = Jinja2Templates(directory="src/templates")

@router_profiles.get("/", response_class=HTMLResponse)
async def profiles(request: Request):
    req = ReqWeb()
    data_specialists = await req.get_active_specialists_data()
    data = {}
    for s in data_specialists:
        work_photos = await req.get_photo(s.id, SpecialistPhotoType.WORKS)
        work_photos = work_photos[:6]
        data[s.id] = work_photos

    return templates.TemplateResponse(
        "profiles.html",
        {"request": request, "title": "Специалисты", "specialists": data_specialists, "spec_photos_map": data}
    )



# @router_profiles.post("/messages")
# async def create_user_message(
#     msg: schemas.UserMessageCreate,
#     db: AsyncSession = Depends(get_db),
#     #current_user: models.User = Depends(get_current_user),
# ):
#     print("RAW MESSAGE:", msg.dict())
#     db_msg = models.UserMessage(
#         user_id=msg.user_id,         #TODO: # берём из JWT
#         specialist_id=msg.specialist_id,
#         message=msg.message,
#         created_at=datetime.now(UTC_PLUS_5),
#         is_valid=None,
#     )
#
#     print(db_msg)
#
#     db.add(db_msg)
#     await db.commit()
#     await db.refresh(db_msg)
#
#     return {"status": "ok", "id": db_msg.id}

#
# @router_profiles.post("/messages")
# async def create_user_message(
#     request: Request,
#     db: AsyncSession = Depends(db.get_db),
# ):
#     raw = await request.body()
#     print("RAW REQUEST BODY:", raw.decode(), flush=True)
#
#     return {"status": "debug"}

from fastapi import Request
import sys

db = DataBase()

@router_profiles.post("/messages")
async def create_user_message(
    msg: schemas.UserMessageCreate,
    db: AsyncSession = Depends(db.get_db),
):
    # начало текущего часа
    start_of_hour = datetime.now(UTC_PLUS_5).replace(minute=0, second=0, microsecond=0).replace(tzinfo=None)
    end_of_hour = start_of_hour + timedelta(hours=1)


    req = ReqWeb()
    cnt_messages = await req.get_cnt_messages(msg.user_id, start_of_hour, end_of_hour)
    if  cnt_messages >= MESSAGES_TO_SPECIALISTS_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Слишком много сообщений, попробуйте позже."
        )



    db_msg = models.UserMessage(
        user_id=msg.user_id,         #TODO: # берём из JWT
        specialist_id=msg.specialist_id,
        message=msg.message,
        created_at=datetime.now(UTC_PLUS_5).replace(microsecond=0).replace(tzinfo=None),
        is_valid=None,
    )

    print(db_msg)

    db.add(db_msg)
    await db.commit()
    await db.refresh(db_msg)

    return {"status": "ok", "id": db_msg.id}



@router_profiles.post("/log_alert")
async def log_alert(req: Request):
    data = await req.json()
    message = data.get("message", "")
    timestamp = datetime.now().isoformat()
    print('!!!!!!!!Alert!!!!!!!!!!!!!!!!!')
    with open("logs/alerts.txt", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")

    return {"status": "ok"}