from fastapi import Depends
from app.utils.auth import get_current_user
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.note import router as note_router
from app.api.v1.endpoints.user import router as user_router

def include_auth_router(app):
    app.include_router(auth_router, prefix="/public", tags=["auth"])

def include_note_router(app):
    app.include_router(note_router, prefix="/notes", tags=["note"], dependencies=[Depends(get_current_user)])

def include_user_router(app):
    app.include_router(user_router, prefix="/user", tags=["user"], dependencies=[Depends(get_current_user)])

def include_routers(app):
    include_auth_router(app)
    include_note_router(app)
    include_user_router(app)