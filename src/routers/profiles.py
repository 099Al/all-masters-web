import json
import os
from datetime import datetime, timedelta
from math import ceil

import hmac
import hashlib
import time
from urllib.parse import parse_qsl

from urllib import request

from fastapi import APIRouter, Request, Depends, Response, Query, Path
from fastapi.responses import HTMLResponse

from fastapi.templating import Jinja2Templates
from fastapi import HTTPException, status
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session


from starlette.responses import FileResponse

from src.config import settings
from src.config_paramaters import configs
from src.database.models import SpecialistPhotoType, models
from src.database.requests_web import ReqWeb
from src.database.connect import DataBase

import mimetypes

from src.schemas import schemas
from src.schemas.schemas import MessageCreate

import src.log_settings
import logging
logger = logging.getLogger(__name__)
#logger = logging.getLogger("uvicorn.access")


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

@router_profiles.get("/{service_id}", response_class=HTMLResponse)
async def profiles(request: Request, service_id: int = Path(..., ge=1), page: int = Query(1, ge=1)):
    req = ReqWeb()
    data_specialists = await req.get_active_specialists_data(service_id)

    total = len(data_specialists)
    total_pages = max(1, ceil(total / configs.PAGINATION_PER_PAGE))

    if page > total_pages:
        page = total_pages

    start = (page - 1) * configs.PAGINATION_PER_PAGE
    end = start + configs.PAGINATION_PER_PAGE
    specialists_page = data_specialists[start:end]

    spec_photos_map = {}
    for s in specialists_page:
        work_photos = await req.get_photo(s.id, SpecialistPhotoType.WORKS)
        spec_photos_map[s.id] = work_photos[:6]

    return templates.TemplateResponse(
        "profiles.html",
        {
            "request": request,
            "title": "Специалисты",
            "specialists": specialists_page,  # <— only current page
            "spec_photos_map": spec_photos_map,  # <— map for visible ones
            "page": page,
            "per_page": configs.PAGINATION_PER_PAGE,
            "total": total,
            "total_pages": total_pages,
            "MODE": settings.MODE,
        }
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

def _verify_telegram_init_data(init_data: str, bot_token: str, max_age_sec: int = 3600) -> dict:
    """
    Verify Telegram WebApp initData signature.
    Returns parsed data dict (values are strings) if valid, else raises.
    """
    if not init_data:
        raise HTTPException(401, "Telegram initData required")

    # Parse querystring-like initData into list of pairs, preserving all fields
    pairs = parse_qsl(init_data, keep_blank_values=True)

    data = dict(pairs)
    received_hash = data.pop("hash", None)
    if not received_hash:
        raise HTTPException(401, "Telegram initData hash missing")

    # Optional: freshness check
    auth_date_str = data.get("auth_date")
    if not auth_date_str or not auth_date_str.isdigit():
        raise HTTPException(401, "Telegram initData auth_date missing/invalid")

    auth_date = int(auth_date_str)
    now = int(time.time())
    if now - auth_date > max_age_sec:
        raise HTTPException(401, "Telegram initData expired")

    # Build data_check_string: key=value lines sorted by key
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))

    # Secret key = HMAC_SHA256("WebAppData", bot_token)
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()

    # Calculated hash = HMAC_SHA256(secret_key, data_check_string)
    calculated_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise HTTPException(401, "Invalid Telegram initData signature")

    return data

async def get_current_tg_user(request: Request):
    #if settings.MODE == "DEV":
    #    return {"id": settings.SUPER_ADMIN_ID}

    init_data = request.headers.get("X-Telegram-Init-Data")
    data = _verify_telegram_init_data(init_data, bot_token=settings.BOT_TOKEN, max_age_sec=3600)

    user_raw = data.get("user")
    if not user_raw:
        raise HTTPException(401, "Telegram initData has no user")

    try:
        user = json.loads(user_raw)
    except json.JSONDecodeError:
        raise HTTPException(401, "Telegram user JSON invalid")

    if "id" not in user:
        raise HTTPException(401, "Telegram user id missing")
    try:
        user["id"] = int(user["id"])
    except (TypeError, ValueError):
        raise HTTPException(401, "Telegram user id is not int")

    return user


db = DataBase()

@router_profiles.post("/messages/list", response_model=list[schemas.MessageOut], status_code=status.HTTP_200_OK,)
async def list_user_messages(
    payload: schemas.MessagesListIn,
    tg_user: int = Depends(get_current_tg_user),
    session: AsyncSession = Depends(db.get_db),
):
    from sqlalchemy import select

    user_id = tg_user["id"]
    print(user_id)
    print(type(user_id))
    specialist_id = payload.specialist_id

    q = (
        select(models.UserMessage)
        .where(
            models.UserMessage.user_id == user_id,
            models.UserMessage.specialist_id == specialist_id,
        )
        .order_by(models.UserMessage.created_at.desc())
    )
    rows = (await session.execute(q)).scalars().all()
    return [
        schemas.MessageOut(
            id=r.id,
            user_id=r.user_id,
            specialist_id=r.specialist_id,
            message=r.message,
            created_at=r.created_at,
        )
        for r in rows
    ]


@router_profiles.post(
    "/messages/create",
    response_model=schemas.MessageOut,  # <- return the object the UI needs
    status_code=status.HTTP_201_CREATED
)
async def create_user_message(
    msg: schemas.MessageCreate,
    tg_user=Depends(get_current_tg_user),
    session: AsyncSession = Depends(db.get_db),
):
    user_id = tg_user["id"]

    # начало текущего часа
    now_local = datetime.now(configs.UTC_PLUS_5)
    start_of_hour = now_local.replace(minute=0, second=0, microsecond=0).replace(tzinfo=None)
    end_of_hour = start_of_hour + timedelta(hours=1)


    req = ReqWeb()
    cnt_messages = await req.get_cnt_messages(user_id, start_of_hour, end_of_hour)
    if cnt_messages >= configs.MESSAGES_TO_SPECIALISTS_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Слишком много сообщений, попробуйте позже."
        )



    db_msg = models.UserMessage(
        user_id=user_id,         #TODO: # берём из JWT
        specialist_id=msg.specialist_id,
        message=msg.message,
        created_at=datetime.now(configs.UTC_PLUS_5).replace(microsecond=0).replace(tzinfo=None),
        is_valid=None,
    )

    session.add(db_msg)
    await session.commit()
    await session.refresh(db_msg)

    return schemas.MessageOut(
        id=db_msg.id,
        user_id=db_msg.user_id,
        specialist_id=db_msg.specialist_id,
        message=db_msg.message,
        created_at=db_msg.created_at
    )


@router_profiles.put("/messages/{msg_id}", response_model=schemas.MessageOut)
async def update_user_message(
    msg_id: int,
    payload: schemas.MessageUpdate,          # message: str
    session: AsyncSession = Depends(db.get_db),
):
    stmt = (
        update(models.UserMessage)
        .where(models.UserMessage.id == msg_id)
        .values(message=payload.message)
        .returning(
            models.UserMessage.id,
            models.UserMessage.user_id,
            models.UserMessage.specialist_id,
            models.UserMessage.message,
            models.UserMessage.created_at,
        )
    )

    res = await session.execute(stmt)
    row = res.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Message not found")

    await session.commit()  # <-- без этого изменения не сохранятся!

    return schemas.MessageOut(
        id=row["id"],
        user_id=row["user_id"],
        specialist_id=row["specialist_id"],
        message=row["message"],
        created_at=row["created_at"],
    )


@router_profiles.delete("/messages/{msg_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_message(
    msg_id: int,
    session: AsyncSession = Depends(db.get_db),
):
    msg = await session.get(models.UserMessage, msg_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    await session.delete(msg)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router_profiles.post("/log_alert")
async def log_alert(req: Request):
    data = await req.json()
    message = data.get("message", "")
    timestamp = datetime.now().isoformat()
    print('!!!!!!!!Alert!!!!!!!!!!!!!!!!!')
    with open("logs/alerts.txt", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")

    return {"status": "ok"}