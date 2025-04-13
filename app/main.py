from fastapi import FastAPI
from app.routers.router import include_routers
from fastapi_pagination import add_pagination

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