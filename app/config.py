from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Task Management API"

    # JWT Settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # PostgreSQL Settings
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str

    # Redis Settings
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_URL: str = f"redis://{REDIS_HOST}:{REDIS_PORT}"

    # Cache Settings
    CACHE_EXPIRE_IN_SECONDS: int = 60

    # Rate Limiting Settings
    RATE_LIMIT_DEFAULT: str = "60/minute"
    RATE_LIMIT_TOKEN: str = "10/minute"
    RATE_LIMIT_CREATE_USER: str = "5/minute"
    RATE_LIMIT_CREATE_TASK: str = "30/minute"
    RATE_LIMIT_READ_TASKS: str = "60/minute"
    RATE_LIMIT_READ_TASK: str = "120/minute"

    # OpenTelemetry Settings
    ENVIRONMENT: str = "development"
    OTLP_ENDPOINT: str = "http://jaeger:4317"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    class Config:
        env_file = ".env"


settings = Settings()  # type: ignore[call-arg]
