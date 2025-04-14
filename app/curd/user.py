from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.model import User

async def get_user_by_email(db: AsyncSession, email: str):
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, email: str, username: str, hashed_password: str):
    new_user = User(email=email, username=username, password=hashed_password, avatar="app/static/avatar/default.jpg")
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user