from datetime import timedelta

from fastapi import Depends, FastAPI, HTTPException, status, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
from jose import JWTError, jwt
from redis import asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from functools import wraps

from . import crud, models, schemas
from .config import settings
from .database import engine, get_db
from .telemetry import setup_telemetry

# Create the FastAPI app
app = FastAPI(title=settings.PROJECT_NAME)

# Setup OpenTelemetry and instrument FastAPI
tracer_provider = setup_telemetry()
tracer_provider.instrument_fastapi(
    app
)  # Instrument FastAPI before adding other middleware

# Get a tracer for manual instrumentation
tracer = trace.get_tracer(__name__)


# Create a custom cache decorator that includes tracing
def traced_cache(expire=settings.CACHE_EXPIRE_IN_SECONDS):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            with tracer.start_as_current_span(f"cache_{func.__name__}") as span:
                # Extract request info if available
                request = None
                current_user = None
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                    # Try to find current_user in args

                for key, value in kwargs.items():
                    if key == "current_user":
                        current_user = value

                # Add user info to span if available
                if current_user:
                    add_user_to_span(span, current_user)

                # Add cache operation details
                span.set_attribute("cache.operation", "get_or_execute")
                span.set_attribute("cache.function", func.__name__)

                # Try to get from cache first
                cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
                span.set_attribute("cache.key", cache_key)

                # Call the original cache decorator
                cached_func = cache(expire=expire)(func)
                result = await cached_func(*args, **kwargs)

                # Add result info to span
                span.set_attribute(
                    "cache.hit", True
                )  # Assuming hit, actual logic would be more complex

                return result

        return wrapper

    return decorator


# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@app.on_event("startup")
async def startup() -> None:
    # Initialize Redis cache
    redis = aioredis.from_url(
        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
        encoding="utf8",
        decode_responses=True,
    )
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")

    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

    # Instrument other components
    tracer_provider.instrument_other(engine)


@app.middleware("http")
async def add_trace_headers(request: Request, call_next):
    """Middleware to ensure trace context is properly propagated and add user info to spans"""
    current_span = trace.get_current_span()

    # Try to extract user info from the token if present
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "")
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            username = payload.get("sub")
            if username:
                # Add username to the current span
                current_span.set_attribute("user.username", username)
        except JWTError:
            # If token is invalid, we just don't add the user info
            pass

    # Add request path and method to span
    current_span.set_attribute("http.route", request.url.path)
    current_span.set_attribute("http.method", request.method)

    # Continue with the request
    response = await call_next(request)

    # Add response status to span
    current_span.set_attribute("http.status_code", response.status_code)

    # Set span status based on response
    if response.status_code >= 400:
        current_span.set_status(Status(StatusCode.ERROR))

    return response


async def get_current_user(
    db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username = payload.get("sub")
        if username is None or not isinstance(username, str):
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = await crud.get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
    return user


def add_user_to_span(span, user):
    """Helper function to add user information to a span"""
    if user:
        span.set_attribute("user.id", user.id)
        span.set_attribute("user.username", user.username)


@app.get("/tasks", response_model=list[schemas.Task])
@traced_cache(expire=settings.CACHE_EXPIRE_IN_SECONDS)
async def read_tasks(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user),
):
    with tracer.start_as_current_span("read_tasks") as span:
        add_user_to_span(span, current_user)
        span.set_attribute("tasks.skip", skip)
        span.set_attribute("tasks.limit", limit)

        tasks = await crud.get_tasks(db, skip=skip, limit=limit)
        span.set_attribute("tasks.count", len(tasks))
        return tasks


@app.get("/tasks/{task_id}", response_model=schemas.Task)
@traced_cache(expire=settings.CACHE_EXPIRE_IN_SECONDS)
async def read_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user),
):
    with tracer.start_as_current_span("read_task") as span:
        add_user_to_span(span, current_user)
        span.set_attribute("task.id", task_id)

        task = await crud.get_task(db, task_id=task_id)
        if task is None:
            span.set_status(Status(StatusCode.ERROR))
            span.set_attribute("error.type", "TaskNotFound")
            raise HTTPException(status_code=404, detail="Task not found")
        return task


@app.post("/tasks", response_model=schemas.Task)
async def create_task(
    task: schemas.TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user),
):
    with tracer.start_as_current_span("create_task") as span:
        add_user_to_span(span, current_user)
        span.set_attribute("task.title", task.title)

        new_task = await crud.create_task(db, task=task, user_id=current_user.id)
        span.set_attribute("task.id", new_task.id)
        return new_task


@app.put("/tasks/{task_id}", response_model=schemas.Task)
async def update_task(
    task_id: int,
    task: schemas.TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user),
):
    with tracer.start_as_current_span("update_task") as span:
        add_user_to_span(span, current_user)
        span.set_attribute("task.id", task_id)

        updated_task = await crud.update_task(db, task_id=task_id, task=task)
        if updated_task is None:
            span.set_status(Status(StatusCode.ERROR))
            span.set_attribute("error.type", "TaskNotFound")
            raise HTTPException(status_code=404, detail="Task not found")
        return updated_task


@app.delete("/tasks/{task_id}", response_model=schemas.Task)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user),
):
    with tracer.start_as_current_span("delete_task") as span:
        add_user_to_span(span, current_user)
        span.set_attribute("task.id", task_id)

        deleted_task = await crud.delete_task(db, task_id=task_id)
        if deleted_task is None:
            span.set_status(Status(StatusCode.ERROR))
            span.set_attribute("error.type", "TaskNotFound")
            raise HTTPException(status_code=404, detail="Task not found")
        return deleted_task


@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    db: AsyncSession = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    with tracer.start_as_current_span("login_for_access_token") as span:
        span.set_attribute("auth.username", form_data.username)

        user = await crud.authenticate_user(db, form_data.username, form_data.password)
        if not user:
            span.set_status(Status(StatusCode.ERROR))
            span.set_attribute("error.type", "AuthenticationFailed")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Add user info to span after successful authentication
        add_user_to_span(span, user)

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = crud.create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}


@app.post("/users", response_model=schemas.User)
async def create_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    with tracer.start_as_current_span("create_user") as span:
        span.set_attribute("new_user.username", user.username)

        db_user = await crud.create_user(db=db, user=user)
        if db_user is None:
            span.set_status(Status(StatusCode.ERROR))
            span.set_attribute("error.type", "UserAlreadyExists")
            raise HTTPException(status_code=400, detail="Username already registered")

        # Add new user info to span
        span.set_attribute("new_user.id", db_user.id)
        return db_user
