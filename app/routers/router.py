from fastapi import Depends
from app.utils.auth import get_current_user
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.note import router as note_router
from app.api.v1.endpoints.user import router as user_router
from app.api.v1.endpoints.aichat import router as aichat_router
from app.api.v1.endpoints.article import router as article_router
from app.api.v1.endpoints.articleDB import router as articleDB_router
from app.api.v1.endpoints.group import router as group_router

def include_auth_router(app):
    app.include_router(auth_router, prefix="/public", tags=["auth"])

def include_note_router(app):
    app.include_router(note_router, prefix="/notes", tags=["note"], dependencies=[Depends(get_current_user)])

def include_user_router(app):
    app.include_router(user_router, prefix="/user", tags=["user"], dependencies=[Depends(get_current_user)])

def include_aichat_router(app):
    app.include_router(aichat_router, prefix="/chat", tags=["aichat"], dependencies=[Depends(get_current_user)])

def include_article_router(app):
    app.include_router(article_router, prefix="/article", tags=["article"], dependencies=[Depends(get_current_user)])

def include_articleDB_router(app):
    app.include_router(articleDB_router, prefix="/database", tags=["articleDB"], dependencies=[Depends(get_current_user)])

def include_group_router(app):
    app.include_router(group_router, prefix="/group", tags=["group"], dependencies=[Depends(get_current_user)])

def include_routers(app):
    include_auth_router(app)
    include_note_router(app)
    include_user_router(app)
    include_aichat_router(app)
    include_article_router(app)
    include_articleDB_router(app)
    include_group_router(app)