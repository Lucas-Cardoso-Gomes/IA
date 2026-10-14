"""
Fast Screen Capture Engine for Jarvis Local Multimodal AI Assistant.
Captures screen frames in a low-overhead background thread, downscales them (e.g., 1080p -> 720p),
and stores the latest frame temporarily on the fast Optane storage path.
"""

import logging
import threading
import time
from pathlib import Path
from typing import Optional, Tuple, Union

from PIL import Image
import mss

from config import BUFFER_PATH, CAPTURE_HEIGHT, CAPTURE_INTERVAL_SEC, CAPTURE_WIDTH, LATEST_FRAME_FILENAME

logger = logging.getLogger(__name__)


class ScreenCaptureEngine:
    """
    Background screen capture worker maintaining low overhead (<15ms target per capture)
    and serving the latest captured frame on-demand to the VLM.
    """

    def __init__(
        self,
        interval_sec: float = CAPTURE_INTERVAL_SEC,
        output_dir: Path = BUFFER_PATH,
        target_resolution: Tuple[int, int] = (CAPTURE_WIDTH, CAPTURE_HEIGHT),
        output_filename: Path = LATEST_FRAME_FILENAME,
    ) -> None:
        """
        Initialize the screen capture engine.

        Args:
            interval_sec: Interval in seconds between background captures.
            output_dir: Fast storage path directory (Optane path).
            target_resolution: Target width and height (width, height) for frame downscaling.
            output_filename: Complete path where the latest frame frame buffer is saved.
        """
        self.interval_sec = interval_sec
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.target_resolution = target_resolution
        self.output_filename = Path(output_filename)

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._latest_image: Optional[Image.Image] = None
        self._lock = threading.Lock()
        self._last_capture_time_ms: float = 0.0

    def start(self) -> None:
        """Start the background screen capture thread."""
        if self._running:
            logger.warning("ScreenCaptureEngine is already running.")
            return

        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        logger.info(f"Screen capture thread started with interval={self.interval_sec}s")

    def stop(self) -> None:
        """Stop the background capture thread gracefully."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info("Screen capture thread stopped.")

    def capture_frame(self) -> Optional[Image.Image]:
        """
        Perform a single low-overhead screen grab, resize frame, save to Optane storage,
        and update in-memory cache.

        Returns:
            PIL Image object of the downscaled screen frame, or synthetic image on headless fallbacks.
        """
        start_t = time.perf_counter()
        try:
            mss_factory = getattr(mss, "MSS", getattr(mss, "mss", None))
            with mss_factory() as sct:
                # Grab primary monitor (monitor 1)
                monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
                sct_img = sct.grab(monitor)
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        except Exception as err:
            logger.debug(f"mss screen capture unavailable or headless display mode: {err}")
            # Synthetic frame fallback for headless / server environments
            img = Image.new("RGB", (1920, 1080), color=(30, 30, 30))

        # Downscale frame to target resolution (e.g. 1280x720)
        if self.target_resolution:
            img = img.resize(self.target_resolution, Image.Resampling.BILINEAR)

        # Atomic update to fast Optane disk storage
        temp_file = self.output_filename.with_suffix(".tmp")
        try:
            img.save(temp_file, "JPEG", quality=85)
            temp_file.replace(self.output_filename)
        except Exception as e:
            logger.error(f"Failed writing frame to fast storage path: {e}")

        # Update latest frame memory
        with self._lock:
            self._latest_image = img.copy()
            self._last_capture_time_ms = (time.perf_counter() - start_t) * 1000.0

        return img

    def get_latest_frame(self) -> Optional[Image.Image]:
        """
        Retrieve the latest captured frame object on-demand for VLM processing.

        Returns:
            The latest PIL Image captured, or performs an on-demand capture if none exists.
        """
        with self._lock:
            if self._latest_image is not None:
                return self._latest_image.copy()

        # If background thread hasn't run yet, capture on-demand
        return self.capture_frame()

    def get_last_capture_latency_ms(self) -> float:
        """Get latency in milliseconds of the last screen capture execution."""
        with self._lock:
            return self._last_capture_time_ms

    def _capture_loop(self) -> None:
        """Background thread execution loop."""
        while self._running:
            self.capture_frame()
            time.sleep(self.interval_sec)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    engine = ScreenCaptureEngine()
    print("Executing single frame capture test...")
    frame = engine.capture_frame()
    print(f"Captured frame size: {frame.size if frame else 'None'}, Latency: {engine.get_last_capture_latency_ms():.2f} ms")
