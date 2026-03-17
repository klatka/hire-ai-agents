from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./hire_agents.db"
    SYNC_DATABASE_URL: str = "sqlite:///./hire_agents.db"
    EXECUTION_TIMEOUT_SECONDS: float = 30.0
    APP_VERSION: str = "0.1.0"
    # Comma-separated origins allowed for CORS.
    # Use "*" to allow all (convenient for demos; restrict in production).
    CORS_ORIGINS: str = "*"

    model_config = {"env_file": ".env", "extra": "ignore"}

    def cors_origins_list(self) -> List[str]:
        """Return CORS_ORIGINS as a list."""
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
