from fastapi import FastAPI, Request
from app.routers.router import include_routers
from fastapi_pagination import add_pagination
from loguru import logger
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

# 注册路由
include_routers(app)

# 注册分页功能
add_pagination(app)

# 设置日志配置
logger.add("app.log", rotation="1 MB", retention="7 days", level="INFO")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许的前端来源
    allow_credentials=True,                  # 允许发送凭据（如 Cookies 或 Authorization 头）
    allow_methods=["*"],                     # 允许的 HTTP 方法
    allow_headers=["*"],                     # 允许的请求头
)

from pathlib import Path
is_github_actions = os.environ.get("GITHUB_ACTIONS") == "true"

if is_github_actions:
    # GitHub Actions 环境 - 使用项目内临时目录
    BASE_DIR = Path(__file__).resolve().parent.parent
    AVATAR_DIR = os.path.join(BASE_DIR, "static", "avatar")
    IMAGES_DIR = os.path.join(BASE_DIR, "static", "images")
else:
    # 生产环境 - 使用实际云存储目录
    AVATAR_DIR = "/lhcos-data/avatar"
    IMAGES_DIR = "/lhcos-data/images"

# 确保目录存在
os.makedirs(AVATAR_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

# 挂载静态文件目录
app.mount("/lhcos-data/avatar", StaticFiles(directory=AVATAR_DIR), name="avatar")
app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")