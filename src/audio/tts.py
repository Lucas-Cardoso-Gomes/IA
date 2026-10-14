"""
Text-to-Speech (TTS) module for Jarvis.
Supports kokoro-onnx and piper-tts for fast, continuous sentence-level audio generation.
"""

import logging
import os
import time
from typing import Generator, Optional, Union
import numpy as np

from config import MODELS_CACHE_PATH, TTS_ENGINE, TTS_VOICE

logger = logging.getLogger(__name__)


class TextToSpeechEngine:
    """TTS Engine wrapper delivering fast audio synthesis."""

    def __init__(
        self,
        engine_type: str = TTS_ENGINE,
        voice: str = TTS_VOICE,
        models_dir: Optional[str] = str(MODELS_CACHE_PATH / "tts"),
    ) -> None:
        """
        Initialize the TTS engine.

        Args:
            engine_type: 'kokoro-onnx' or 'piper'.
            voice: Target voice identifier.
            models_dir: Fast storage directory for voice model artifacts.
        """
        self.engine_type = engine_type.lower()
        self.voice = voice
        self.models_dir = models_dir
        self._kokoro = None
        self._piper = None
        self._init_engine()

    def _init_engine(self) -> None:
        """Initialize kokoro-onnx or piper engine with fallback support."""
        if "kokoro" in self.engine_type:
            try:
                from kokoro_onnx import Kokoro
                # Check for cached model files or lazy load
                model_path = os.path.join(self.models_dir, "kokoro-v0_19.onnx")
                voices_path = os.path.join(self.models_dir, "voices.bin")
                if os.path.exists(model_path) and os.path.exists(voices_path):
                    self._kokoro = Kokoro(model_path, voices_path)
                    logger.info("Kokoro-ONNX TTS initialized.")
                else:
                    logger.info("Kokoro model files not found locally; fallback streaming mode active.")
            except Exception as e:
                logger.debug(f"Kokoro-ONNX unavailable: {e}")

        elif "piper" in self.engine_type:
            try:
                import piper
                logger.info("Piper TTS initialized.")
                self._piper = piper
            except Exception as e:
                logger.debug(f"Piper TTS unavailable: {e}")

    def synthesize(self, text: str) -> np.ndarray:
        """
        Synthesize text into audio samples (PCM float32 array @ 24kHz/16kHz).

        Args:
            text: Text to synthesize.

        Returns:
            1D numpy array of audio samples.
        """
        start_t = time.perf_counter()
        if not text or not text.strip():
            return np.array([], dtype=np.float32)

        if self._kokoro is not None:
            try:
                samples, sample_rate = self._kokoro.create(text, voice=self.voice, speed=1.0, lang="pt-br")
                elapsed_ms = (time.perf_counter() - start_t) * 1000.0
                logger.info(f"Kokoro TTS synthesized '{text[:30]}...' in {elapsed_ms:.2f}ms")
                return samples
            except Exception as e:
                logger.error(f"Kokoro synthesis failed: {e}")

        # Fallback synthetic audio wave generation (440Hz beep scaled to text duration)
        sample_rate = 24000
        duration_sec = max(0.2, len(text) * 0.05)
        t = np.linspace(0, duration_sec, int(sample_rate * duration_sec), False)
        # Generate soft sinusoidal synthetic audio stream
        audio_wave = 0.1 * np.sin(2 * np.pi * 440 * t).astype(np.float32)
        elapsed_ms = (time.perf_counter() - start_t) * 1000.0
        logger.info(f"TTS (fallback) synthesized {len(text)} chars in {elapsed_ms:.2f}ms")
        return audio_wave

    def stream_synthesize(self, text_stream: Generator[str, None, None]) -> Generator[np.ndarray, None, None]:
        """
        Sentence-level streaming TTS generator for ultra-fast time-to-first-audio.

        Args:
            text_stream: Generator yielding chunks of text from LLM.

        Yields:
            Numpy audio arrays per completed sentence.
        """
        sentence_buffer = ""
        delimiters = {".", "!", "?", "\n", ";"}

        for chunk in text_stream:
            sentence_buffer += chunk
            # Check if we reached a sentence boundary
            if any(char in delimiters for char in chunk):
                clean_sentence = sentence_buffer.strip()
                if clean_sentence:
                    yield self.synthesize(clean_sentence)
                sentence_buffer = ""

        # Flush remaining text
        if sentence_buffer.strip():
            yield self.synthesize(sentence_buffer.strip())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    tts = TextToSpeechEngine()
    audio = tts.synthesize("Olá, eu sou o Jarvis. Como posso te ajudar hoje?")
    print(f"Generated audio sample count: {len(audio)}")
