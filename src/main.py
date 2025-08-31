import os
from typing import Union

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.routers.profiles import router_profiles
from src.routers.static_text import router_text

app = FastAPI()

app.include_router(router_text)
app.include_router(router_profiles)



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
    uvicorn.run(app="main:app", reload=True, host='127.0.0.1', port=8000, workers=2)