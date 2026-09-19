"""Application Settings and Configuration."""
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

from app.schemas.enums import NetworkPolicy


class Settings(BaseSettings):
    """Global Application and Sandbox Settings."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Application Basics
    APP_NAME: str = "ReRun Autonomous Coding Platform"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8000", "http://127.0.0.1:8000", "http://localhost:3000", "*"]

    # Storage Paths
    BASE_DIR: Path = Path(__file__).resolve().parents[3]
    WORKSPACE_DIR: Path = BASE_DIR / "workspaces"
    ARTIFACTS_DIR: Path = BASE_DIR / "artifacts_store"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./rerun.db"

    # Sandbox Resource Policies (Configurable)
    MAX_EXECUTION_TIME: int = Field(default=30, description="Max runtime in seconds per execution")
    MAX_TOTAL_TASK_TIME: int = Field(default=180, description="Max total wall-clock seconds per task")
    MAX_MEMORY_MB: int = Field(default=512, description="Max memory in MB per container")
    MAX_CPU_CORES: float = Field(default=1.0, description="Max CPU quota")
    MAX_OUTPUT_SIZE_BYTES: int = Field(default=524288, description="Max output stream bytes (512 KB)")
    MAX_FILE_SIZE_BYTES: int = Field(default=52428800, description="Max file size for artifacts (50 MB)")
    MAX_RETRIES: int = Field(default=3, description="Max repair attempts before stopping")
    REPEATED_FAILURE_THRESHOLD: int = Field(default=2, description="Consecutive identical failures before replan/stop")
    NETWORK_POLICY: NetworkPolicy = NetworkPolicy.DISABLED
    NETWORK_ALLOWLIST: List[str] = []

    # Sandbox Engine Configuration
    DOCKER_IMAGE: str = "rerun-sandbox:latest"
    DOCKER_HOST: Optional[str] = None
    ALLOW_LOCAL_FALLBACK_FOR_TESTING: bool = Field(
        default=True,
        description="Strictly for offline CI and dev testing when Docker daemon is not active. Never used for untrusted production workloads."
    )

    # LLM Settings
    LLM_PROVIDER: str = Field(default="gemini", description="mock, openai, gemini, or ollama")
    LLM_MODEL: str = "gemini-3.6-flash"
    LLM_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    LLM_TEMPERATURE: float = 0.2
    LLM_MAX_TOKENS: int = 4096
    LLM_TIMEOUT: int = 60
    MAX_LLM_CALLS_PER_TASK: int = 15

    # Concurrency
    MAX_CONCURRENT_TASKS: int = 4


settings = Settings()

# Ensure directories exist
settings.WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
settings.ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
