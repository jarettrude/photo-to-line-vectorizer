"""
U²-Net portrait segmentation model.

Implements U²-Net for subject isolation and background removal.
Uses pre-trained weights from the official repository.
"""

import logging
from pathlib import Path
from typing import Tuple

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image

from utils.device import device_manager

logger = logging.getLogger(__name__)


class REBNCONV(nn.Module):
    """ReLU + Batch Norm + Conv block."""

    def __init__(self, in_ch: int, out_ch: int, dirate: int = 1):
        super().__init__()
        self.conv_s1 = nn.Conv2d(
            in_ch, out_ch, 3, padding=1 * dirate, dilation=1 * dirate
        )
        self.bn_s1 = nn.BatchNorm2d(out_ch)
        self.relu_s1 = nn.ReLU(inplace=True)

    def forward(self, x):
        return self.relu_s1(self.bn_s1(self.conv_s1(x)))


class RSU7(nn.Module):
    """Residual U-block with 7 layers."""

    def __init__(self, in_ch: int, mid_ch: int, out_ch: int):
        super().__init__()
        self.rebnconvin = REBNCONV(in_ch, out_ch)
        self.rebnconv1 = REBNCONV(out_ch, mid_ch)
        self.pool1 = nn.MaxPool2d(2, stride=2, ceil_mode=True)
        self.rebnconv2 = REBNCONV(mid_ch, mid_ch)
        self.pool2 = nn.MaxPool2d(2, stride=2, ceil_mode=True)
        self.rebnconv3 = REBNCONV(mid_ch, mid_ch)
        self.pool3 = nn.MaxPool2d(2, stride=2, ceil_mode=True)
        self.rebnconv4 = REBNCONV(mid_ch, mid_ch)
        self.pool4 = nn.MaxPool2d(2, stride=2, ceil_mode=True)
        self.rebnconv5 = REBNCONV(mid_ch, mid_ch)
        self.pool5 = nn.MaxPool2d(2, stride=2, ceil_mode=True)
        self.rebnconv6 = REBNCONV(mid_ch, mid_ch)
        self.rebnconv7 = REBNCONV(mid_ch, mid_ch)
        self.rebnconv6d = REBNCONV(mid_ch * 2, mid_ch)
        self.rebnconv5d = REBNCONV(mid_ch * 2, mid_ch)
        self.rebnconv4d = REBNCONV(mid_ch * 2, mid_ch)
        self.rebnconv3d = REBNCONV(mid_ch * 2, mid_ch)
        self.rebnconv2d = REBNCONV(mid_ch * 2, mid_ch)
        self.rebnconv1d = REBNCONV(mid_ch * 2, out_ch)

    def forward(self, x):
        hx = x
        hxin = self.rebnconvin(hx)
        hx1 = self.rebnconv1(hxin)
        hx = self.pool1(hx1)
        hx2 = self.rebnconv2(hx)
        hx = self.pool2(hx2)
        hx3 = self.rebnconv3(hx)
        hx = self.pool3(hx3)
        hx4 = self.rebnconv4(hx)
        hx = self.pool4(hx4)
        hx5 = self.rebnconv5(hx)
        hx = self.pool5(hx5)
        hx6 = self.rebnconv6(hx)
        hx7 = self.rebnconv7(hx6)
        hx6d = self.rebnconv6d(torch.cat((hx7, hx6), 1))
        hx6dup = F.interpolate(
            hx6d, size=hx5.shape[2:], mode="bilinear", align_corners=False
        )
        hx5d = self.rebnconv5d(torch.cat((hx6dup, hx5), 1))
        hx5dup = F.interpolate(
            hx5d, size=hx4.shape[2:], mode="bilinear", align_corners=False
        )
        hx4d = self.rebnconv4d(torch.cat((hx5dup, hx4), 1))
        hx4dup = F.interpolate(
            hx4d, size=hx3.shape[2:], mode="bilinear", align_corners=False
        )
        hx3d = self.rebnconv3d(torch.cat((hx4dup, hx3), 1))
        hx3dup = F.interpolate(
            hx3d, size=hx2.shape[2:], mode="bilinear", align_corners=False
        )
        hx2d = self.rebnconv2d(torch.cat((hx3dup, hx2), 1))
        hx2dup = F.interpolate(
            hx2d, size=hx1.shape[2:], mode="bilinear", align_corners=False
        )
        hx1d = self.rebnconv1d(torch.cat((hx2dup, hx1), 1))
        return hx1d + hxin


class RSU4(nn.Module):
    """Residual U-block with 4 layers."""

    def __init__(self, in_ch: int, mid_ch: int, out_ch: int):
        super().__init__()
        self.rebnconvin = REBNCONV(in_ch, out_ch)
        self.rebnconv1 = REBNCONV(out_ch, mid_ch)
        self.pool1 = nn.MaxPool2d(2, stride=2, ceil_mode=True)
        self.rebnconv2 = REBNCONV(mid_ch, mid_ch)
        self.pool2 = nn.MaxPool2d(2, stride=2, ceil_mode=True)
        self.rebnconv3 = REBNCONV(mid_ch, mid_ch)
        self.pool3 = nn.MaxPool2d(2, stride=2, ceil_mode=True)
        self.rebnconv4 = REBNCONV(mid_ch, mid_ch)
        self.rebnconv3d = REBNCONV(mid_ch * 2, mid_ch)
        self.rebnconv2d = REBNCONV(mid_ch * 2, mid_ch)
        self.rebnconv1d = REBNCONV(mid_ch * 2, out_ch)

    def forward(self, x):
        hx = x
        hxin = self.rebnconvin(hx)
        hx1 = self.rebnconv1(hxin)
        hx = self.pool1(hx1)
        hx2 = self.rebnconv2(hx)
        hx = self.pool2(hx2)
        hx3 = self.rebnconv3(hx)
        hx = self.pool3(hx3)
        hx4 = self.rebnconv4(hx)
        hx3d = self.rebnconv3d(torch.cat((hx4, hx3), 1))
        hx3dup = F.interpolate(
            hx3d, size=hx2.shape[2:], mode="bilinear", align_corners=False
        )
        hx2d = self.rebnconv2d(torch.cat((hx3dup, hx2), 1))
        hx2dup = F.interpolate(
            hx2d, size=hx1.shape[2:], mode="bilinear", align_corners=False
        )
        hx1d = self.rebnconv1d(torch.cat((hx2dup, hx1), 1))
        return hx1d + hxin


class U2NETP(nn.Module):
    """U²-Net Portrait model architecture (lightweight version)."""

    def __init__(self, in_ch: int = 3, out_ch: int = 1):
        super().__init__()
        self.stage1 = RSU7(in_ch, 16, 64)
        self.pool12 = nn.MaxPool2d(2, stride=2, ceil_mode=True)
        self.stage2 = RSU7(64, 16, 64)
        self.pool23 = nn.MaxPool2d(2, stride=2, ceil_mode=True)
        self.stage3 = RSU7(64, 16, 64)
        self.pool34 = nn.MaxPool2d(2, stride=2, ceil_mode=True)
        self.stage4 = RSU7(64, 16, 64)
        self.pool45 = nn.MaxPool2d(2, stride=2, ceil_mode=True)
        self.stage5 = RSU4(64, 16, 64)
        self.pool56 = nn.MaxPool2d(2, stride=2, ceil_mode=True)
        self.stage6 = RSU4(64, 16, 64)
        self.stage5d = RSU4(128, 16, 64)
        self.stage4d = RSU7(128, 16, 64)
        self.stage3d = RSU7(128, 16, 64)
        self.stage2d = RSU7(128, 16, 64)
        self.stage1d = RSU7(128, 16, 64)
        self.side1 = nn.Conv2d(64, out_ch, 3, padding=1)
        self.side2 = nn.Conv2d(64, out_ch, 3, padding=1)
        self.side3 = nn.Conv2d(64, out_ch, 3, padding=1)
        self.side4 = nn.Conv2d(64, out_ch, 3, padding=1)
        self.side5 = nn.Conv2d(64, out_ch, 3, padding=1)
        self.side6 = nn.Conv2d(64, out_ch, 3, padding=1)
        self.outconv = nn.Conv2d(6, out_ch, 1)

    def forward(self, x):
        hx = x
        hx1 = self.stage1(hx)
        hx = self.pool12(hx1)
        hx2 = self.stage2(hx)
        hx = self.pool23(hx2)
        hx3 = self.stage3(hx)
        hx = self.pool34(hx3)
        hx4 = self.stage4(hx)
        hx = self.pool45(hx4)
        hx5 = self.stage5(hx)
        hx = self.pool56(hx5)
        hx6 = self.stage6(hx)
        hx6up = F.interpolate(
            hx6, size=hx5.shape[2:], mode="bilinear", align_corners=False
        )
        hx5d = self.stage5d(torch.cat((hx6up, hx5), 1))
        hx5dup = F.interpolate(
            hx5d, size=hx4.shape[2:], mode="bilinear", align_corners=False
        )
        hx4d = self.stage4d(torch.cat((hx5dup, hx4), 1))
        hx4dup = F.interpolate(
            hx4d, size=hx3.shape[2:], mode="bilinear", align_corners=False
        )
        hx3d = self.stage3d(torch.cat((hx4dup, hx3), 1))
        hx3dup = F.interpolate(
            hx3d, size=hx2.shape[2:], mode="bilinear", align_corners=False
        )
        hx2d = self.stage2d(torch.cat((hx3dup, hx2), 1))
        hx2dup = F.interpolate(
            hx2d, size=hx1.shape[2:], mode="bilinear", align_corners=False
        )
        hx1d = self.stage1d(torch.cat((hx2dup, hx1), 1))
        d1 = self.side1(hx1d)
        d2 = self.side2(hx2d)
        d2 = F.interpolate(d2, size=d1.shape[2:], mode="bilinear", align_corners=False)
        d3 = self.side3(hx3d)
        d3 = F.interpolate(d3, size=d1.shape[2:], mode="bilinear", align_corners=False)
        d4 = self.side4(hx4d)
        d4 = F.interpolate(d4, size=d1.shape[2:], mode="bilinear", align_corners=False)
        d5 = self.side5(hx5d)
        d5 = F.interpolate(d5, size=d1.shape[2:], mode="bilinear", align_corners=False)
        d6 = self.side6(hx6)
        d6 = F.interpolate(d6, size=d1.shape[2:], mode="bilinear", align_corners=False)
        d0 = self.outconv(torch.cat((d1, d2, d3, d4, d5, d6), 1))
        return (
            torch.sigmoid(d0),
            torch.sigmoid(d1),
            torch.sigmoid(d2),
            torch.sigmoid(d3),
            torch.sigmoid(d4),
            torch.sigmoid(d5),
            torch.sigmoid(d6),
        )


class U2NetPredictor:
    """
    U²-Net portrait segmentation predictor.

    Loads pre-trained U²-Net model and provides high-level interface
    for subject isolation from backgrounds.
    """

    def __init__(self, model_path: Path):
        """
        Initialize U²-Net predictor with model weights.

        Args:
            model_path: Path to .pth model weights file
        """
        self.model_path = model_path
        self.model = U2NETP(3, 1)
        self._load_weights()
        self.model = device_manager.to_device(self.model)
        self.model.eval()
        logger.info(f"U²-Net model loaded from {model_path}")

    def _load_weights(self) -> None:
        """Load model weights from file with proper error handling."""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model weights not found: {self.model_path}")

        state_dict = torch.load(self.model_path, map_location="cpu")
        self.model.load_state_dict(state_dict)

    @torch.no_grad()
    def predict(self, image: np.ndarray) -> np.ndarray:
        """
        Generate segmentation mask for input image.

        Args:
            image: Input RGB image as numpy array (H, W, 3), range [0, 255]

        Returns:
            Binary mask as numpy array (H, W), range [0, 255]
        """
        original_size = image.shape[:2]
        image_tensor = self._preprocess(image)
        image_tensor = device_manager.to_device(image_tensor)

        d0, *_ = self.model(image_tensor)

        mask = d0[0, 0].cpu().numpy()
        mask = (mask * 255).astype(np.uint8)
        mask = cv2.resize(
            mask, (original_size[1], original_size[0]), interpolation=cv2.INTER_LINEAR
        )

        return mask

    def _preprocess(self, image: np.ndarray) -> torch.Tensor:
        """
        Preprocess image for model input.

        Args:
            image: RGB numpy array (H, W, 3)

        Returns:
            Preprocessed tensor (1, 3, 512, 512)
        """
        image = cv2.resize(image, (512, 512), interpolation=cv2.INTER_LINEAR)
        image = image.astype(np.float32) / 255.0
        image = (image - np.array([0.485, 0.456, 0.406])) / np.array(
            [0.229, 0.224, 0.225]
        )
        image = image.transpose(2, 0, 1)
        return torch.from_numpy(image).unsqueeze(0).float()

    def isolate_subject(self, image: np.ndarray, threshold: int = 128) -> np.ndarray:
        """
        Extract subject from background using segmentation mask.

        Args:
            image: Input RGB image (H, W, 3)
            threshold: Mask threshold for binary segmentation

        Returns:
            RGBA image with background removed (H, W, 4)
        """
        mask = self.predict(image)
        mask_binary = (mask > threshold).astype(np.uint8) * 255

        if image.shape[2] == 3:
            alpha = mask_binary
            result = np.dstack((image, alpha))
        else:
            result = image.copy()
            result[:, :, 3] = mask_binary

        return result
