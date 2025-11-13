"""
Pydantic models for API request/response schemas.

Defines all data structures for API communication.
"""
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ProcessingMode(str, Enum):
    """Processing mode selection."""

    AUTO = "auto"
    PORTRAIT = "portrait"
    ANIMAL = "animal"
    CUSTOM = "custom"


class ProcessingStatus(str, Enum):
    """Processing job status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class UploadResponse(BaseModel):
    """Response from image upload."""

    job_id: str = Field(..., description="Unique job identifier")
    filename: str = Field(..., description="Original filename")
    image_url: str = Field(..., description="URL to uploaded image")


class ProcessParams(BaseModel):
    """Parameters for image processing."""

    canvas_width_mm: float = Field(..., description="Canvas width in millimeters", gt=0)
    canvas_height_mm: float = Field(..., description="Canvas height in millimeters", gt=0)
    line_width_mm: float = Field(..., description="Line width in millimeters", gt=0)
    isolate_subject: bool = Field(default=False, description="Whether to isolate subject from background")
    use_ml: bool = Field(default=False, description="Whether to use ML-based line extraction")
    edge_threshold: tuple[int, int] = Field(default=(50, 150), description="Canny edge thresholds")
    line_threshold: int = Field(default=16, description="Vectorization line threshold")
    merge_tolerance: float = Field(default=0.5, description="Path merge tolerance in mm")
    simplify_tolerance: float = Field(default=0.2, description="Path simplification tolerance in mm")
    hatching_enabled: bool = Field(default=False, description="Enable hatching for dark areas")
    hatch_density: float = Field(default=2.0, description="Hatching density factor")
    hatch_angle: int = Field(default=45, description="Hatching angle in degrees")
    darkness_threshold: int = Field(default=100, description="Threshold for dark region hatching")


class ProcessRequest(BaseModel):
    """Request to process an uploaded image."""

    job_id: str = Field(..., description="Job ID from upload")
    mode: ProcessingMode = Field(default=ProcessingMode.AUTO, description="Processing mode")
    params: Optional[ProcessParams] = Field(default=None, description="Custom processing parameters")


class ProcessResponse(BaseModel):
    """Response from process initiation."""

    job_id: str = Field(..., description="Job identifier")
    status: ProcessingStatus = Field(..., description="Current status")
    message: str = Field(default="Processing started", description="Status message")


class JobStats(BaseModel):
    """Statistics about processed SVG."""

    path_count: int = Field(..., description="Number of paths in SVG")
    total_length_mm: float = Field(..., description="Total path length in mm")
    width_mm: Optional[float] = Field(None, description="SVG width in mm")
    height_mm: Optional[float] = Field(None, description="SVG height in mm")


class JobStatusResponse(BaseModel):
    """Response from status query."""

    job_id: str = Field(..., description="Job identifier")
    status: ProcessingStatus = Field(..., description="Current status")
    progress: int = Field(default=0, description="Progress percentage (0-100)")
    result_url: Optional[str] = Field(None, description="URL to result SVG if complete")
    stats: Optional[JobStats] = Field(None, description="Processing statistics if complete")
    error: Optional[str] = Field(None, description="Error message if failed")
    device_used: Optional[str] = Field(None, description="Device used for processing")


class WebSocketMessage(BaseModel):
    """WebSocket progress message."""

    type: str = Field(..., description="Message type: progress, complete, error")
    job_id: str = Field(..., description="Job identifier")
    stage: Optional[str] = Field(None, description="Current processing stage")
    percent: Optional[int] = Field(None, description="Progress percentage")
    message: Optional[str] = Field(None, description="Status message")
    result_url: Optional[str] = Field(None, description="Result URL if complete")
