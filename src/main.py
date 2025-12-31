import os
from typing import Union

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles

from src.routers.profiles import router_profiles
from src.routers.static_text import router_text
from src.config import settings

app = FastAPI()

app.include_router(router_text)
app.include_router(router_profiles)


# class CachingStaticFiles(StaticFiles):
#     async def get_response(self, path, scope):
#         response: FileResponse = await super().get_response(path, scope)
#         # Кэширование на 30 дней
#         response.headers["Cache-Control"] = "public, max-age=2592000"
#         return response

app.mount("/static", StaticFiles(directory="src/static"), name="static")
app.mount("/images/defaults", StaticFiles(directory="images/defaults", follow_symlink=True), name="defaults")
app.mount("/images/works", StaticFiles(directory="images/works", follow_symlink=True), name="works")



@app.get("/")
async def read_root():
    return {"Hello": "World!"}


templates_errors = Jinja2Templates(directory="src/templates")

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return templates_errors.TemplateResponse(
            "errors/404.html",
            {"request": request, "title": "Страница не найдена"}
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


if __name__ == "__main__":
    """
    Функция находится в src/main.py
    В путях в роутерах и директориях src не надо прописывать
    Реагирует на замену в html файлах, на изменения в путях к файлм не реагирует
    """
    print(os.getpid())
    uvicorn.run(app="src.main:app", reload=True, host=settings.WEB_HOST, port=settings.WEB_PORT, workers=2)

    #локальный запуск
    #uvicorn.run(app="main:app", reload=True, host=settings.WEB_HOST, port=settings.WEB_PORT, workers=2)