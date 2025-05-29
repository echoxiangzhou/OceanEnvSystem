from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    # 项目基本信息
    PROJECT_NAME: str = "Ocean Environment System"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # MySQL数据库配置
    MYSQL_SERVER: str = os.getenv("MYSQL_SERVER", "localhost")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "oceanenv_user")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "iocas6760")
    MYSQL_DB: str = os.getenv("MYSQL_DB", "oceanenv_metadata")
    MYSQL_CHARSET: str = os.getenv("MYSQL_CHARSET", "utf8mb4")
    SQLALCHEMY_DATABASE_URI: Optional[str] = None

    @property
    def get_database_url(self) -> str:
        if self.SQLALCHEMY_DATABASE_URI:
            return self.SQLALCHEMY_DATABASE_URI
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_SERVER}:{self.MYSQL_PORT}/{self.MYSQL_DB}?charset={self.MYSQL_CHARSET}"

    # Redis配置
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    
    # 安全配置
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # 数据目录配置
    DATA_DIR: Path = Path("data")
    UPLOAD_DIR: Path = DATA_DIR / "uploads"
    PROCESSED_DIR: Path = DATA_DIR / "processed"
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()

# 确保必要的目录存在
settings.DATA_DIR.mkdir(exist_ok=True)
settings.UPLOAD_DIR.mkdir(exist_ok=True)
settings.PROCESSED_DIR.mkdir(exist_ok=True)
