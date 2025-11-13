"""
Application configuration management using pydantic-settings.

Loads environment variables and provides typed configuration objects
for the application.
"""
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings can be overridden via environment variables.
    Supports .env file loading automatically.
    """

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    # File Storage
    upload_dir: Path = Path("./temp/uploads")
    results_dir: Path = Path("./temp/results")
    max_upload_size_mb: int = 50

    # Models
    u2net_model_path: Path = Path("../models/u2net/pytorch/u2netp.pth")
    informative_drawings_model_path: Path = Path("../models/informative-drawings/checkpoints/netG_A_sketch.pth")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def ensure_directories(self) -> None:
        """Create required directories if they don't exist."""
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_directories()
