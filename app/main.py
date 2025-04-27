from fastapi import FastAPI, Request
from app.routers.router import include_routers
from fastapi_pagination import add_pagination
from loguru import logger

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