"""
Application configuration management using pydantic-settings v2.

Leverages Python 3.14's deferred annotation evaluation (PEP 649)
and Pydantic v2's strict type validation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with strict type validation.

    Uses Pydantic v2 features for enhanced type safety and validation.
    All settings can be overridden via environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",  # Strict: no extra fields allowed
        validate_default=True,
        frozen=False,
    )

    # Server Configuration
    host: Annotated[str, Field(description="Server host address")] = "0.0.0.0"
    port: Annotated[int, Field(ge=1, le=65535, description="Server port")] = 8000
    debug: Annotated[bool, Field(description="Debug mode flag")] = True

    # File Storage
    upload_dir: Annotated[Path, Field(description="Upload directory path")] = Path("./temp/uploads")
    results_dir: Annotated[Path, Field(description="Results directory path")] = Path("./temp/results")
    max_upload_size_mb: Annotated[int, Field(ge=1, le=500, description="Max upload size in MB")] = 50

    # Model Paths
    u2net_model_path: Annotated[
        Path,
        Field(description="Path to U²-Net model weights"),
    ] = Path("../models/u2net/pytorch/u2netp.pth")

    informative_drawings_model_path: Annotated[
        Path,
        Field(description="Path to Informative Drawings model"),
    ] = Path("../models/informative-drawings/checkpoints/netG_A_sketch.pth")

    @field_validator("upload_dir", "results_dir")
    @classmethod
    def validate_directory_paths(cls, v: Path) -> Path:
        """Ensure directory paths are absolute and normalized."""
        return v.resolve()

    def ensure_directories(self) -> None:
        """Create required directories if they don't exist."""
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_directories()
