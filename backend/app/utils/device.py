"""
Hardware acceleration device detection and management.

Leverages Python 3.14's free-threaded execution and modern type hints.
Auto-detects available compute devices in priority order:
CUDA (NVIDIA) → MPS (Apple Metal) → CPU fallback.
"""

from __future__ import annotations

import logging
from enum import StrEnum
from typing import TYPE_CHECKING

import torch

if TYPE_CHECKING:
    from torch import nn

logger = logging.getLogger(__name__)


class DeviceType(StrEnum):
    """Available compute device types using Python 3.14 StrEnum."""

    CUDA = "cuda"
    MPS = "mps"
    CPU = "cpu"


class DeviceManager:
    """
    Manages hardware acceleration device selection and lifecycle.

    Detects available devices on initialization and provides
    a consistent interface for moving models and tensors to
    the optimal device.

    Uses Python 3.14 features for improved performance and type safety.
    """

    def __init__(self) -> None:
        """Initialize device manager and auto-detect available hardware."""
        self._device = self._detect_device()
        logger.info(f"Using device: {self._device.type} ({self.device_name})")

    def _detect_device(self) -> torch.device:
        """
        Auto-detect optimal compute device.

        Returns device in priority order:
        1. CUDA (NVIDIA GPUs)
        2. MPS (Apple Silicon Metal)
        3. CPU (fallback)

        Returns:
            torch.device: Selected compute device
        """
        if torch.cuda.is_available():
            return torch.device("cuda")
        if torch.backends.mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")

    @property
    def device(self) -> torch.device:
        """Get the currently selected device."""
        return self._device

    @property
    def device_type(self) -> DeviceType:
        """Get the device type as enum."""
        return DeviceType(self._device.type)

    @property
    def device_name(self) -> str:
        """
        Get human-readable device name with details.

        Returns:
            str: Formatted device name with hardware details
        """
        match self._device.type:
            case "cuda":
                return f"CUDA ({torch.cuda.get_device_name(0)})"
            case "mps":
                return "Apple Metal (MPS)"
            case _:
                return "CPU"

    def to_device(
        self, tensor_or_model: torch.Tensor | nn.Module
    ) -> torch.Tensor | nn.Module:
        """
        Move tensor or model to the selected device.

        Args:
            tensor_or_model: PyTorch tensor or nn.Module

        Returns:
            Tensor or model moved to device
        """
        return tensor_or_model.to(self._device)


# Global device manager instance
device_manager = DeviceManager()
