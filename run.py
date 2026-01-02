import uvicorn
from src.config import settings

if __name__ == "__main__":
    """
    Функция старта находится в src/main.py
    В путях в роутерах и директориях src не надо прописывать
    Реагирует на замену в html файлах, на изменения в путях к файлм не реагирует
    uvicorn.run(app="main:app", reload=True, host='127.0.0.1', port=8000, workers=2)
    
        
    Если вынести на уровень с src, то нужно указывать src в пути
    uvicorn.run(app="src.main:app", reload=True, host='127.0.0.1', port=8000, workers=2)
    """

    uvicorn.run(
        app="src.main:app",
        reload=True,
        host=settings.WEB_HOST,
        port=settings.WEB_PORT,
        workers=1,
        #log_level="info",
        # ssl_certfile="certs/cert.pem",
        # ssl_keyfile="certs/key.pem"
    )