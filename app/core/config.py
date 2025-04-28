import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "JieNote Backend" # 项目名称
    VERSION: str = "1.0.0" # 项目版本
    SQLALCHEMY_DATABASE_URL = "mysql+asyncmy://root:oneapi@47.93.172.156:3306/JieNote"  # 替换为实际的用户名、密码和数据库名称
    SECRET_KEY: str = os.getenv("SECRET_KEY", "default_secret_key")  # JWT密钥
    ALGORITHM: str = "HS256" # JWT算法
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440 # token过期时间
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 刷新token过期时间7天
    SMTP_SERVER: str = "smtp.163.com" # SMTP服务器
    SMTP_PORT: int = 465 # SMTP端口
    SENDER_EMAIL : str = "jienote_buaa@163.com"
    SENDER_PASSWORD: str = os.getenv("SENDER_PASSWORD", "default_password") # 发件人邮箱密码
    KIMI_API_KEY: str = os.getenv("KIMI_API_KEY", "default_kimi_api_key") # KIMI API密钥


settings = Settings()