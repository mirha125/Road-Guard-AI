from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path

# Get the backend directory path
BACKEND_DIR = Path(__file__).parent
ENV_FILE = BACKEND_DIR / ".env"

class Settings(BaseSettings):
    MONGO_URI: str
    DB_NAME: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ADMIN_EMAIL: str
    ADMIN_PASSWORD: str
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_FROM_NAME: str
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    class Config:
        env_file = str(ENV_FILE)
        env_file_encoding = 'utf-8'

print(f"Loading .env from: {ENV_FILE}")
print(f".env file exists: {ENV_FILE.exists()}")
settings = Settings()