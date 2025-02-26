from datetime import datetime, timedelta
from typing import Optional

from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from opentelemetry import trace

from . import models, schemas
from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
tracer = trace.get_tracer(__name__)


async def get_task(db: AsyncSession, task_id: int) -> Optional[models.Task]:
    with tracer.start_as_current_span("db_get_task") as span:
        span.set_attribute("db.operation", "get_task")
        span.set_attribute("db.task_id", task_id)

        result = await db.execute(select(models.Task).filter(models.Task.id == task_id))
        task = result.scalar_one_or_none()

        if task:
            span.set_attribute("db.task.found", True)
            span.set_attribute("db.task.owner_id", task.owner_id)
        else:
            span.set_attribute("db.task.found", False)

        return task


async def get_tasks(
    db: AsyncSession, skip: int = 0, limit: int = 10
) -> list[models.Task]:
    with tracer.start_as_current_span("db_get_tasks") as span:
        span.set_attribute("db.operation", "get_tasks")
        span.set_attribute("db.skip", skip)
        span.set_attribute("db.limit", limit)

        result = await db.execute(select(models.Task).offset(skip).limit(limit))
        tasks = list(result.scalars().all())

        span.set_attribute("db.tasks.count", len(tasks))
        return tasks


async def create_task(
    db: AsyncSession, task: schemas.TaskCreate, user_id: int
) -> models.Task:
    with tracer.start_as_current_span("db_create_task") as span:
        span.set_attribute("db.operation", "create_task")
        span.set_attribute("db.user_id", user_id)
        span.set_attribute("db.task.title", task.title)

        db_task = models.Task(
            title=task.title,
            description=task.description,
            status=task.status,
            owner_id=user_id,
        )
        db.add(db_task)
        await db.commit()
        await db.refresh(db_task)

        span.set_attribute("db.task.id", db_task.id)
        return db_task


async def update_task(
    db: AsyncSession, task_id: int, task: schemas.TaskUpdate
) -> Optional[models.Task]:
    with tracer.start_as_current_span("db_update_task") as span:
        span.set_attribute("db.operation", "update_task")
        span.set_attribute("db.task_id", task_id)

        db_task = await get_task(db, task_id=task_id)
        if db_task is None:
            span.set_attribute("db.task.found", False)
            return None

        span.set_attribute("db.task.found", True)

        # Update task fields
        update_data = task.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_task, key, value)
            span.set_attribute(f"db.task.update.{key}", str(value))

        db_task.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(db_task)
        return db_task


async def delete_task(db: AsyncSession, task_id: int) -> Optional[models.Task]:
    with tracer.start_as_current_span("db_delete_task") as span:
        span.set_attribute("db.operation", "delete_task")
        span.set_attribute("db.task_id", task_id)

        db_task = await get_task(db, task_id=task_id)
        if db_task is None:
            span.set_attribute("db.task.found", False)
            return None

        span.set_attribute("db.task.found", True)
        span.set_attribute("db.task.owner_id", db_task.owner_id)

        await db.delete(db_task)
        await db.commit()
        return db_task


async def get_user_by_username(
    db: AsyncSession, username: str
) -> Optional[models.User]:
    with tracer.start_as_current_span("db_get_user_by_username") as span:
        span.set_attribute("db.operation", "get_user_by_username")
        span.set_attribute("db.username", username)

        result = await db.execute(
            select(models.User).filter(models.User.username == username)
        )
        user = result.scalar_one_or_none()

        if user:
            span.set_attribute("db.user.found", True)
            span.set_attribute("db.user.id", user.id)
        else:
            span.set_attribute("db.user.found", False)

        return user


async def create_user(
    db: AsyncSession, user: schemas.UserCreate
) -> Optional[models.User]:
    with tracer.start_as_current_span("db_create_user") as span:
        span.set_attribute("db.operation", "create_user")
        span.set_attribute("db.username", user.username)

        # Check if user already exists
        existing_user = await get_user_by_username(db, username=user.username)
        if existing_user:
            span.set_attribute("db.user.already_exists", True)
            return None

        span.set_attribute("db.user.already_exists", False)

        hashed_password = pwd_context.hash(user.password)
        db_user = models.User(username=user.username, hashed_password=hashed_password)
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)

        span.set_attribute("db.user.id", db_user.id)
        return db_user


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


async def authenticate_user(db: AsyncSession, username: str, password: str):
    with tracer.start_as_current_span("db_authenticate_user") as span:
        span.set_attribute("db.operation", "authenticate_user")
        span.set_attribute("db.username", username)

        user = await get_user_by_username(db, username)
        if not user:
            span.set_attribute("auth.success", False)
            span.set_attribute("auth.failure_reason", "user_not_found")
            return False

        if not verify_password(password, user.hashed_password):
            span.set_attribute("auth.success", False)
            span.set_attribute("auth.failure_reason", "invalid_password")
            return False

        span.set_attribute("auth.success", True)
        span.set_attribute("auth.user.id", user.id)
        return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    with tracer.start_as_current_span("create_access_token") as span:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        to_encode.update({"exp": expire})

        span.set_attribute("token.username", data.get("sub", "unknown"))
        span.set_attribute("token.expires_at", expire.isoformat())

        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return encoded_jwt
