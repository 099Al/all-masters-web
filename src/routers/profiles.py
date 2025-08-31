from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from pathlib import Path

from fastapi.templating import Jinja2Templates

from src.database.requests_web import ReqWeb

router_profiles = APIRouter(
    prefix="/profiles",
    tags=["profile"],
)


templates = Jinja2Templates(directory="src/templates")

@router_profiles.get("/", response_class=HTMLResponse)
async def profiles(request: Request):
    req = ReqWeb()
    data_specialists = await req.get_active_specialists_data()
    return templates.TemplateResponse(
        "profiles.html",
        {"request": request, "title": "Специалисты", "specialists": data_specialists}
    )
