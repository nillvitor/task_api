from datetime import datetime, timedelta
from typing import Optional

from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from . import models, schemas
from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def get_task(db: AsyncSession, task_id: int) -> Optional[models.Task]:
    result = await db.execute(select(models.Task).filter(models.Task.id == task_id))
    return result.scalar_one_or_none()


async def get_tasks(
    db: AsyncSession, skip: int = 0, limit: int = 10
) -> list[models.Task]:
    result = await db.execute(select(models.Task).offset(skip).limit(limit))
    return list(result.scalars().all())


async def create_task(
    db: AsyncSession, task: schemas.TaskCreate, user_id: int
) -> models.Task:
    db_task = models.Task(
        title=task.title,
        description=task.description,
        status=task.status,
        owner_id=user_id,
    )
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    return db_task


async def update_task(
    db: AsyncSession, task_id: int, task: schemas.TaskUpdate
) -> Optional[models.Task]:
    db_task = await get_task(db, task_id)
    if db_task is None:
        return None

    for field, value in task.dict().items():
        setattr(db_task, field, value)

    await db.commit()
    await db.refresh(db_task)
    return db_task


async def delete_task(db: AsyncSession, task_id: int) -> bool:
    db_task = await get_task(db, task_id)
    if db_task is None:
        return False

    await db.delete(db_task)
    await db.commit()
    return True


async def get_user_by_username(
    db: AsyncSession, username: str
) -> Optional[models.User]:
    result = await db.execute(
        select(models.User).filter(models.User.username == username)
    )
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user: schemas.UserCreate) -> models.User:
    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


async def authenticate_user(db: AsyncSession, username: str, password: str):
    user = await get_user_by_username(db, username)
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt
