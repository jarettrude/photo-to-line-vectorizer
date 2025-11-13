"""
Pydantic models for API request/response schemas.

Uses Pydantic v2 with strict validation and Python 3.14 type hints.
Defines all data structures for API communication.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field, field_validator


class ProcessingMode(StrEnum):
    """Processing mode selection."""

    AUTO = "auto"
    PORTRAIT = "portrait"
    ANIMAL = "animal"
    CUSTOM = "custom"


class ProcessingStatus(StrEnum):
    """Processing job status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class UploadResponse(BaseModel):
    """Response from image upload."""

    model_config = {"frozen": True, "extra": "forbid"}

    job_id: Annotated[str, Field(description="Unique job identifier", min_length=1)]
    filename: Annotated[str, Field(description="Original filename", min_length=1)]
    image_url: Annotated[str, Field(description="URL to uploaded image", min_length=1)]


class ProcessParams(BaseModel):
    """
    Parameters for image processing.

    All canvas and line width parameters are required (no defaults).
    """

    model_config = {"extra": "forbid", "validate_default": True}

    canvas_width_mm: Annotated[float, Field(description="Canvas width in millimeters", gt=0, le=5000)]
    canvas_height_mm: Annotated[float, Field(description="Canvas height in millimeters", gt=0, le=5000)]
    line_width_mm: Annotated[float, Field(description="Line width in millimeters", gt=0, le=10)]

    isolate_subject: Annotated[
        bool,
        Field(default=False, description="Whether to isolate subject from background"),
    ]
    use_ml: Annotated[bool, Field(default=False, description="Whether to use ML-based line extraction")]

    edge_threshold: Annotated[
        tuple[int, int],
        Field(default=(50, 150), description="Canny edge thresholds (low, high)"),
    ]
    line_threshold: Annotated[int, Field(default=16, description="Vectorization line threshold", ge=1, le=255)]

    merge_tolerance: Annotated[float, Field(default=0.5, description="Path merge tolerance in mm", ge=0, le=10)]
    simplify_tolerance: Annotated[
        float,
        Field(default=0.2, description="Path simplification tolerance in mm", ge=0, le=10)
    ]

    hatching_enabled: Annotated[bool, Field(default=False, description="Enable hatching for dark areas")]
    hatch_density: Annotated[float, Field(default=2.0, description="Hatching density factor", gt=0, le=10)]
    hatch_angle: Annotated[int, Field(default=45, description="Hatching angle in degrees", ge=-180, le=180)]
    darkness_threshold: Annotated[
        int,
        Field(default=100, description="Threshold for dark region hatching", ge=0, le=255)
    ]

    @field_validator("edge_threshold")
    @classmethod
    def validate_edge_threshold(cls, v: tuple[int, int]) -> tuple[int, int]:
        """Ensure low threshold is less than high threshold."""
        low, high = v
        if not (0 <= low < high <= 255):
            raise ValueError("Edge threshold must be 0 <= low < high <= 255")
        return v


class ProcessRequest(BaseModel):
    """Request to process an uploaded image."""

    model_config = {"extra": "forbid"}

    job_id: Annotated[str, Field(description="Job ID from upload", min_length=1)]
    mode: Annotated[ProcessingMode, Field(default=ProcessingMode.AUTO, description="Processing mode")]
    params: Annotated[ProcessParams | None, Field(default=None, description="Custom processing parameters")]


class ProcessResponse(BaseModel):
    """Response from process initiation."""

    model_config = {"frozen": True}

    job_id: Annotated[str, Field(description="Job identifier")]
    status: Annotated[ProcessingStatus, Field(description="Current status")]
    message: Annotated[str, Field(default="Processing started", description="Status message")]


class JobStats(BaseModel):
    """Statistics about processed SVG."""

    model_config = {"frozen": True}

    path_count: Annotated[int, Field(description="Number of paths in SVG", ge=0)]
    total_length_mm: Annotated[float, Field(description="Total path length in mm", ge=0)]
    width_mm: Annotated[float | None, Field(default=None, description="SVG width in mm")]
    height_mm: Annotated[float | None, Field(default=None, description="SVG height in mm")]


class JobStatusResponse(BaseModel):
    """Response from status query."""

    model_config = {"extra": "forbid"}

    job_id: Annotated[str, Field(description="Job identifier")]
    status: Annotated[ProcessingStatus, Field(description="Current status")]
    progress: Annotated[int, Field(default=0, description="Progress percentage (0-100)", ge=0, le=100)]
    result_url: Annotated[str | None, Field(default=None, description="URL to result SVG if complete")]
    stats: Annotated[JobStats | None, Field(default=None, description="Processing statistics if complete")]
    error: Annotated[str | None, Field(default=None, description="Error message if failed")]
    device_used: Annotated[str | None, Field(default=None, description="Device used for processing")]


class WebSocketMessage(BaseModel):
    """WebSocket progress message."""

    model_config = {"extra": "forbid"}

    type: Annotated[str, Field(description="Message type: progress, complete, error", pattern="^(progress|complete|error)$")]
    job_id: Annotated[str, Field(description="Job identifier")]
    stage: Annotated[str | None, Field(default=None, description="Current processing stage")]
    percent: Annotated[int | None, Field(default=None, description="Progress percentage", ge=0, le=100)]
    message: Annotated[str | None, Field(default=None, description="Status message")]
    result_url: Annotated[str | None, Field(default=None, description="Result URL if complete")]
