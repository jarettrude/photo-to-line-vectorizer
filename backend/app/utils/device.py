"""
Hardware acceleration device detection and management.

Auto-detects available compute devices in priority order:
CUDA (NVIDIA) → MPS (Apple Metal) → CPU fallback.
"""
import logging
from enum import Enum

import torch

logger = logging.getLogger(__name__)


class DeviceType(str, Enum):
    """Available compute device types."""

    CUDA = "cuda"
    MPS = "mps"
    CPU = "cpu"


class DeviceManager:
    """
    Manages hardware acceleration device selection and lifecycle.

    Detects available devices on initialization and provides
    a consistent interface for moving models and tensors to
    the optimal device.
    """

    def __init__(self):
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
        """
        if torch.cuda.is_available():
            return torch.device("cuda")
        elif torch.backends.mps.is_available():
            return torch.device("mps")
        else:
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
        """Get human-readable device name with details."""
        if self._device.type == "cuda":
            return f"CUDA ({torch.cuda.get_device_name(0)})"
        elif self._device.type == "mps":
            return "Apple Metal (MPS)"
        else:
            return "CPU"

    def to_device(self, tensor_or_model):
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
