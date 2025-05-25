from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.model import User
from app.schemas.user import UserUpdate

async def get_user_by_email(db: AsyncSession, email: str):
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, email: str, username: str, hashed_password: str):
    new_user = User(email=email, username=username, password=hashed_password, avatar="/lhcos-data/avatar/default.png")
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

async def update_user_in_db(db: AsyncSession, user_update: UserUpdate, user_id: int):
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user:
        if user_update.username:
            user.username = user_update.username
        if user_update.address:
            user.address = user_update.address
        if user_update.university:
            user.university = user_update.university
        if user_update.introduction:
            user.introduction = user_update.introduction
        user.avatar = user_update.avatar
        await db.commit()
        await db.refresh(user)
    return user

async def update_user_password(db: AsyncSession, user_id: int, hashed_password: str):
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user:
        user.password = hashed_password
        await db.commit()
        await db.refresh(user)
    return user
