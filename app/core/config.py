class Settings:
    PROJECT_NAME: str = "JieNote Backend"
    VERSION: str = "1.0.0"
    SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:coders007@47.93.172.156:3306/JieNote"  # 替换为实际的用户名、密码和数据库名称

settings = Settings()