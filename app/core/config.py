from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./hire_agents.db"
    SYNC_DATABASE_URL: str = "sqlite:///./hire_agents.db"
    EXECUTION_TIMEOUT_SECONDS: float = 30.0
    APP_VERSION: str = "0.1.0"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
