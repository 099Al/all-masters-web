import os

from urllib import request

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from fastapi.templating import Jinja2Templates
from fastapi import HTTPException

from starlette.responses import FileResponse

from src.database.requests_web import ReqWeb
import mimetypes

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
    return templates.TemplateResponse(
        "profiles.html",
        {"request": request, "title": "Специалисты", "specialists": data_specialists}
    )
