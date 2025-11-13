"""
Tests for device detection and management.

Validates hardware acceleration device selection logic.
"""

import torch
from utils.device import DeviceManager, DeviceType


def test_device_manager_initialization():
    """Test that DeviceManager initializes correctly."""
    manager = DeviceManager()
    assert manager.device is not None
    assert manager.device_type in [DeviceType.CUDA, DeviceType.MPS, DeviceType.CPU]


def test_device_detection_priority():
    """Test that device detection follows CUDA → MPS → CPU priority."""
    manager = DeviceManager()

    if torch.cuda.is_available():
        assert manager.device_type == DeviceType.CUDA
    elif torch.backends.mps.is_available():
        assert manager.device_type == DeviceType.MPS
    else:
        assert manager.device_type == DeviceType.CPU


def test_device_name():
    """Test that device_name returns human-readable string."""
    manager = DeviceManager()
    device_name = manager.device_name

    assert isinstance(device_name, str)
    assert len(device_name) > 0

    if manager.device_type == DeviceType.CUDA:
        assert "CUDA" in device_name
    elif manager.device_type == DeviceType.MPS:
        assert "MPS" in device_name or "Metal" in device_name
    else:
        assert "CPU" in device_name


def test_to_device_tensor():
    """Test moving tensor to device."""
    manager = DeviceManager()
    tensor = torch.randn(3, 224, 224)

    moved_tensor = manager.to_device(tensor)

    assert moved_tensor.device.type == manager.device.type


def test_to_device_model():
    """Test moving model to device."""
    manager = DeviceManager()
    model = torch.nn.Linear(10, 5)

    moved_model = manager.to_device(model)

    param = next(moved_model.parameters())
    assert param.device.type == manager.device.type
