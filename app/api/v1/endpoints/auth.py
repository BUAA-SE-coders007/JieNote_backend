from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import random
import time
import redis
from email.utils import formataddr

from app.db.session import SessionLocal
from app.models.model import User
from app.schemas.auth import UserCreate, UserLogin, UserSendCode
from app.core.config import settings
from app.curd.user import get_user_by_email, create_user

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# 配置 Redis 连接
while True:
    try:
        print("Connecting to Redis...")
        redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
        redis_client.ping()
        break
    except redis.ConnectionError:
        print("Redis connection failed, retrying...")
        time.sleep(1)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/register", response_model=dict)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = get_user_by_email(db, user.email)
    if (redis_client.exists(f"email:{user.email}:code")):
        code = redis_client.get(f"email:{user.email}:code").decode("utf-8")
        if (user.code != code):
            raise HTTPException(status_code=400, detail="Invalid verification code")
    else:
        raise HTTPException(status_code=400, detail="Verification code expired or not sent")
    
    if (existing_user):
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = pwd_context.hash(user.password)
    create_user(db, user.email, user.username, hashed_password)
    return {"msg": "User registered successfully"}

@router.post("/login", response_model=dict)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, user.email)
    if not db_user or not pwd_context.verify(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", }

# 发送验证码
@router.post("/send_code", response_model=dict)
def send_code(user_send_code : UserSendCode, db: Session = Depends(get_db)):
    # 检查 Redis 中是否存在该邮箱的发送记录
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
    message["From"] = formataddr(("JieNote团队", "noreply@jienote.com"))
    message["To"] = user_send_code.email
    message["Subject"] = Header(subject, 'utf-8').encode()
    # 添加必要的内容传输编码头
    message.add_header('Content-Transfer-Encoding', 'base64')

    try:
        # 连接 SMTP 服务器并发送邮件
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, [user_send_code.email], message.as_string())

        # 将验证码和发送时间存储到 Redis，设置 5 分钟过期时间
        redis_client.setex(f"email:{user_send_code.email}:code", settings.ACCESS_TOKEN_EXPIRE_MINUTES, code)
        redis_client.setex(f"email:{user_send_code.email}:time", settings.ACCESS_TOKEN_EXPIRE_MINUTES, int(time.time()))

        return {"msg": "Verification code sent"}

    except smtplib.SMTPException as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")