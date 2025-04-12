from sqlalchemy.orm import Session
from app.models.model import User

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, email: str, username: str,hashed_password: str):
    new_user = User(email=email, username=username, password=hashed_password, avatar="app/static/avatar/default.jpg")
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user