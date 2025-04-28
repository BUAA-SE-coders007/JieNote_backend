from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt, JWTError, ExpiredSignatureError
import aiosmtplib
from email.mime.text import MIMEText
from email.header import Header
import random
import time
from email.utils import formataddr

from app.schemas.auth import UserCreate, UserLogin, UserSendCode, ReFreshToken
from app.core.config import settings
from app.curd.user import get_user_by_email, create_user
from app.curd.article import crud_self_create_folder, crud_article_statistic
from app.utils.get_db import get_db
from app.utils.redis import get_redis_client
from app.curd.note import find_recent_notes_in_db

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")  # 使用 bcrypt 加密算法
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# 配置 Redis 连接
redis_client = get_redis_client()

async def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def create_refresh_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/register", response_model=dict)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    existing_user = await get_user_by_email(db, user.email)
    if redis_client.exists(f"email:{user.email}:code"):
        code = redis_client.get(f"email:{user.email}:code")
        if user.code != code:
            raise HTTPException(status_code=400, detail="Invalid verification code")
    else:
        raise HTTPException(status_code=400, detail="Verification code expired or not sent")

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = pwd_context.hash(user.password)
    new_user = await create_user(db, user.email, user.username, hashed_password)
    await crud_self_create_folder("", new_user.id, db)
    return {"msg": "User registered successfully"}

@router.post("/login", response_model=dict)
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    db_user = await get_user_by_email(db, user.email)
    if not db_user or not pwd_context.verify(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    access_token = await create_access_token(
        data={"sub": db_user.email, "id": db_user.id}, expires_delta=access_token_expires
    )
    refresh_token = await create_refresh_token(
        data={"sub": db_user.email, "id": db_user.id}, expires_delta=refresh_token_expires
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": db_user.id,
        "email": db_user.email,
        "username": db_user.username,
        "avatar": db_user.avatar
    }

@router.post("/refresh", response_model=dict)
async def refresh_token(refresh_token: ReFreshToken):
    try:
        payload = jwt.decode(refresh_token.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token type")
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = await create_access_token(
            data={"sub": payload["sub"], "id": payload["id"]}, expires_delta=access_token_expires
        )
        return {"access_token": access_token}
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

# 发送验证码
@router.post("/send_code", response_model=dict)
async def send_code(user_send_code: UserSendCode):
    if redis_client.exists(f"email:{user_send_code.email}:time"):
        raise HTTPException(status_code=429, detail="You can only request a verification code once every 5 minutes.")

    # 生成随机验证码
    code = str(random.randint(100000, 999999))

    # SMTP 配置
    smtp_server = settings.SMTP_SERVER
    smtp_port = settings.SMTP_PORT
    sender_email = settings.SENDER_EMAIL 
    sender_password = settings.SENDER_PASSWORD  

    # 邮件内容
    subject = "验证码"
    body = f"欢迎使用JieNote，很开心遇见您，您的验证码是：{code}，请在5分钟内使用。"

    # 创建MIMEText对象时需要显式指定子类型和编码
    message = MIMEText(_text=body, _subtype='plain', _charset='utf-8')
    message["From"] = formataddr(("JieNote团队", "jienote_buaa@163.com"))
    message["To"] = user_send_code.email
    message["Subject"] = Header(subject, 'utf-8').encode()
    # 添加必要的内容传输编码头
    message.add_header('Content-Transfer-Encoding', 'base64')

    try:
        await aiosmtplib.send(
            message,
            hostname=smtp_server,
            port=smtp_port,
            username=sender_email,
            password=sender_password,
            use_tls=True,
        )

        redis_client.setex(f"email:{user_send_code.email}:code", ACCESS_TOKEN_EXPIRE_MINUTES * 60, code)
        redis_client.setex(f"email:{user_send_code.email}:time", ACCESS_TOKEN_EXPIRE_MINUTES * 60, int(time.time()))

        return {"msg": "Verification code sent"}

    except aiosmtplib.SMTPException as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")
    
@router.get("/articleStatistic", response_model="dict")
async def article_statistic(db: AsyncSession = Depends(get_db)):
    articles = await crud_article_statistic(db)
    return {"articles": articles}

@router.get("/recent", response_model=dict)
async def get_recent_notes(db: AsyncSession = Depends(get_db)):
    notes = await find_recent_notes_in_db(db)
    return {
        "notes": notes
    }