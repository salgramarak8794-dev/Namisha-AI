import os
import io
import mss
from PIL import Image
from typing import Optional, Dict, Any

class ScreenCapture:
    def __init__(self):
        self.permission_granted = False

    def request_permission(self) -> bool:
        """Called before capturing. In production, gated by UI prompt."""
        return self.permission_granted

    def set_permission(self, granted: bool):
        self.permission_granted = granted

    def capture_primary_screen(self, resize_ratio: float = 0.5) -> Optional[Image.Image]:
        """
        Captures the primary monitor with downscaling to reduce RAM/LLM bandwidth.
        Never runs unless permission has been explicitly granted.
        """
        if not self.permission_granted:
            raise PermissionError("Screen capture permission was not granted by the user.")

        with mss.mss() as sct:
            monitor = sct.monitors[1]  # Primary monitor
            sct_img = sct.grab(monitor)
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            
            # Downscale for performance & low RAM usage
            if resize_ratio < 1.0:
                new_w = int(img.width * resize_ratio)
                new_h = int(img.height * resize_ratio)
                img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            return img
