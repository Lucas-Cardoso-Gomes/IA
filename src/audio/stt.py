"""
Speech-to-Text (STT) module for Jarvis using faster-whisper.
Optimized for low-latency transcription using CUDA / quantized INT8 or FP16 models.
"""

import logging
import os
import time
from typing import Optional, Union
import numpy as np

from config import MODELS_CACHE_PATH, STT_COMPUTE_TYPE, STT_MODEL_NAME, TARGET_LANGUAGE

logger = logging.getLogger(__name__)


class SpeechToTextEngine:
    """STT Engine leveraging faster-whisper on CUDA/CPU with fallback support."""

    def __init__(
        self,
        model_size_or_path: str = STT_MODEL_NAME,
        device: str = "auto",
        compute_type: str = STT_COMPUTE_TYPE,
        download_root: Optional[str] = str(MODELS_CACHE_PATH / "whisper"),
    ) -> None:
        """
        Initialize the faster-whisper STT model.

        Args:
            model_size_or_path: Whisper model size ('whisper-large-v3-turbo', 'small', etc.).
            device: 'cuda', 'cpu', or 'auto'.
            compute_type: 'int8', 'float16', 'float32', 'int8_float16'.
            download_root: Directory on Optane storage to cache model weights.
        """
        self.model_size_or_path = model_size_or_path
        self.device = device
        self.compute_type = compute_type
        self.download_root = download_root
        self._model = None
        self._load_model()

    def _load_model(self) -> None:
        """Lazy load or initialize faster-whisper model with fallback handling."""
        try:
            from faster_whisper import WhisperModel

            if self.device == "auto":
                import torch
                actual_device = "cuda" if torch.cuda.is_available() else "cpu"
            else:
                actual_device = self.device

            logger.info(f"Loading faster-whisper model '{self.model_size_or_path}' on device={actual_device}...")
            self._model = WhisperModel(
                self.model_size_or_path,
                device=actual_device,
                compute_type=self.compute_type if actual_device == "cuda" else "int8",
                download_root=self.download_root,
            )
            logger.info("faster-whisper model loaded successfully.")
        except Exception as e:
            logger.warning(f"Could not load faster-whisper ({e}). STT will use fallback mode.")
            self._model = None

    def transcribe(self, audio_data: Union[str, np.ndarray], language: str = "pt") -> str:
        """
        Transcribe raw audio waveform or file path into text.

        Args:
            audio_data: Path to audio file or 1D float32 numpy array sampled at 16kHz.
            language: ISO language code (e.g., 'pt' for Portuguese).

        Returns:
            Transcribed text output string.
        """
        start_t = time.perf_counter()
        lang_code = language.split("-")[0].lower() if "-" in language else language

        if self._model is None:
            # Fallback mock transcription for environments without full CUDA/whisper models loaded
            logger.debug("Executing mock STT fallback.")
            if isinstance(audio_data, str):
                return f"[Mock STT from file: {os.path.basename(audio_data)}]"
            return "[Mock STT Audio Prompt]"

        try:
            segments, info = self._model.transcribe(
                audio_data,
                language=lang_code,
                beam_size=1,  # Beam size 1 for ultra-low latency greedy decoding
                vad_filter=True,
            )
            text_result = " ".join([seg.text.strip() for seg in segments]).strip()
            elapsed_ms = (time.perf_counter() - start_t) * 1000.0
            logger.info(f"STT completed in {elapsed_ms:.2f}ms: '{text_result}'")
            return text_result
        except Exception as err:
            logger.error(f"Error during STT transcription: {err}")
            return ""


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    stt = SpeechToTextEngine()
    print("STT Module ready.")
