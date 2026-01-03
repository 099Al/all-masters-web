import os
from pathlib import Path

#from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict



class Settings(BaseSettings):
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    ENGINE: str

    WEB_HOST: str
    WEB_PORT: int

    MODE: str = None

    SUPER_ADMIN_ID: int

    BOT_TOKEN: str

    #instead load_dotenv()
    path_root: str = str(Path(__file__).resolve().parent.parent)
    path_env: str = str(Path(__file__).resolve().parent.parent / '.env')
    model_config = SettingsConfigDict(env_file=path_env, env_file_encoding="utf-8", extra="ignore")

    @property
    def connect_url(self):
        return f'{self.ENGINE}://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}'


settings = Settings()