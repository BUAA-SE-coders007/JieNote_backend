from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.core.config import settings

engine = create_engine(settings.SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)    #连接mysql
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建异步引擎
async_engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

# 创建异步会话
async_session = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False
)