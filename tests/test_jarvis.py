"""
Unit tests for Jarvis core modules.
"""

import unittest
import numpy as np
from PIL import Image

from config import BUFFER_PATH, VECTOR_DB_PATH
from src.vision.capture import ScreenCaptureEngine
from src.memory.rag import ContinuousMemoryRAG
from src.audio.stt import SpeechToTextEngine
from src.audio.tts import TextToSpeechEngine
from src.audio.vad import VoiceActivityDetector
from src.core.router import JarvisRouter


class TestJarvisModules(unittest.TestCase):
    """Test suite covering Jarvis modules."""

    def test_screen_capture(self) -> None:
        """Test frame capture functionality."""
        engine = ScreenCaptureEngine()
        frame = engine.capture_frame()
        self.assertIsNotNone(frame)
        self.assertIsInstance(frame, Image.Image)

    def test_memory_rag(self) -> None:
        """Test adding and querying continuous memory."""
        rag = ContinuousMemoryRAG(table_name="test_memory_table")
        rag.add_memory("Estudando Inteligência Artificial no Optane", context_tags="test")
        results = rag.query_memory("Inteligência Artificial")
        self.assertGreaterEqual(len(results), 1)

    def test_stt_tts_vad(self) -> None:
        """Test STT, TTS, and VAD fallback functions."""
        stt = SpeechToTextEngine()
        tts = TextToSpeechEngine()
        vad = VoiceActivityDetector()

        audio_samples = np.zeros(16000, dtype=np.float32)
        transcript = stt.transcribe(audio_samples)
        self.assertIsInstance(transcript, str)

        audio_output = tts.synthesize("Teste de síntese")
        self.assertGreater(len(audio_output), 0)

        is_speech = vad.is_speech(audio_samples)
        self.assertIsInstance(is_speech, bool)

    def test_router(self) -> None:
        """Test JarvisRouter orchestration and vision detection."""
        router = JarvisRouter()
        self.assertTrue(router.requires_vision("O que é isso na tela?"))
        self.assertFalse(router.requires_vision("Que horas são?"))

        stream = router.process_query_stream("Olá Jarvis")
        response = "".join(list(stream))
        self.assertGreater(len(response), 0)


if __name__ == "__main__":
    unittest.main()
