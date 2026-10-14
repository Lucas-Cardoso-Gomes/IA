"""
Voice Activity Detection (VAD) module for Jarvis.
Uses silero-vad or webrtcvad to detect when active speech occurs.
"""

import logging
from typing import Optional
import numpy as np

from config import VAD_THRESHOLD

logger = logging.getLogger(__name__)


class VoiceActivityDetector:
    """VAD class to identify speech segments from microphone PCM stream."""

    def __init__(self, sample_rate: int = 16000, threshold: float = VAD_THRESHOLD) -> None:
        """
        Initialize VAD detector.

        Args:
            sample_rate: Audio sampling frequency in Hz (typically 16000).
            threshold: Speech probability threshold between 0.0 and 1.0.
        """
        self.sample_rate = sample_rate
        self.threshold = threshold
        self._silero_model = None
        self._init_vad()

    def _init_vad(self) -> None:
        """Initialize Silero VAD model."""
        try:
            import torch
            model, _ = torch.hub.load(
                repo_or_dir="snakers4/silero-vad",
                model="silero_vad",
                force_reload=False,
                onnx=False,
            )
            self._silero_model = model
            logger.info("Silero VAD initialized successfully.")
        except Exception as e:
            logger.debug(f"Silero VAD fallback mode active: {e}")

    def is_speech(self, audio_chunk: np.ndarray) -> bool:
        """
        Determine if an audio chunk contains human speech.

        Args:
            audio_chunk: 1D float32 or int16 numpy array of audio samples.

        Returns:
            True if speech is detected above threshold, False otherwise.
        """
        if len(audio_chunk) == 0:
            return False

        # Convert int16 to float32 normalized [-1.0, 1.0] if needed
        if audio_chunk.dtype == np.int16:
            audio_float = audio_chunk.astype(np.float32) / 32768.0
        else:
            audio_float = audio_chunk.astype(np.float32)

        if self._silero_model is not None:
            try:
                import torch
                tensor_audio = torch.from_numpy(audio_float)
                speech_prob = self._silero_model(tensor_audio, self.sample_rate).item()
                return bool(speech_prob >= self.threshold)
            except Exception as e:
                logger.debug(f"Silero VAD inference error: {e}")

        # Energy-based VAD fallback
        energy = np.mean(audio_float ** 2)
        return bool(energy > 0.005)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    vad = VoiceActivityDetector()
    test_audio = np.random.uniform(-0.1, 0.1, 1600).astype(np.float32)
    print("VAD is_speech test:", vad.is_speech(test_audio))
