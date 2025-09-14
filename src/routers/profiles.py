import os
from datetime import datetime

from urllib import request

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse

from fastapi.templating import Jinja2Templates
from fastapi import HTTPException
from sqlalchemy.orm import Session

from starlette.responses import FileResponse

from src.config_paramaters import UTC_PLUS_5
from src.database.models import SpecialistPhotoType, models
from src.database.requests_web import ReqWeb
from src.database.connect import get_db

import mimetypes

from src.schemas import schemas

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



@router_profiles.post("/messages")
def create_user_message(msg: schemas.UserMessageCreate, db: Session = Depends(get_db)):
    db_msg = models.UserMessage(
        user_id=msg.user_id,
        specialist_id=msg.specialist_id,
        message=msg.message,
        created_at=datetime.now(UTC_PLUS_5),
        is_valid=None
    )
    db.add(db_msg)
    db.commit()
    db.refresh(db_msg)
    return {"status": "ok", "id": db_msg.id}