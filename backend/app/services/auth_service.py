from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.measurement import User


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).one_or_none()


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = get_user_by_username(db, username)
    if user is None or not user.active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def seed_admin_user(db: Session, username: str, password: str, email: str) -> User:
    user = get_user_by_username(db, username)
    if user:
        return user
    user = User(
        username=username,
        full_name="Administrador SGE",
        email=email,
        password_hash=hash_password(password),
        role="admin",
        active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

