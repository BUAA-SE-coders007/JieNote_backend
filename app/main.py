from fastapi import FastAPI
from app.api.v1.endpoints.auth import router as auth_router

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

app.include_router(auth_router, prefix="/public", tags=["auth"])