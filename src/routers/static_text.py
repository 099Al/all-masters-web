from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from pathlib import Path

from fastapi.templating import Jinja2Templates

router_text = APIRouter(
    prefix="/message",
    tags=["text", "message"],
)


templates = Jinja2Templates(directory="src/templates")

@router_text.get("/rules", response_class=HTMLResponse)
async def service_rules(request: Request):
    #html_path = Path("src/templates/rules.html")
    #return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
    return templates.TemplateResponse(
        "rules.html",  # имя шаблона
        {"request": request, "title": "Правила сервиса"}  # context
    )
    # return templates.TemplateResponse(
    #     request=request,
    #     name="rules.html",
    #     context={"title": "Правила сервиса"}
    # )