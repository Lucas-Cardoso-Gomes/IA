"""
Main Entry Point for Jarvis Local Multimodal AI Assistant.
Provides continuous voice/screen loop or interactive CLI mode.
"""

import argparse
import logging
import sys
import time
from typing import Optional

from config import TARGET_LANGUAGE
from src.audio.stt import SpeechToTextEngine
from src.audio.tts import TextToSpeechEngine
from src.audio.vad import VoiceActivityDetector
from src.core.router import JarvisRouter
from src.memory.rag import ContinuousMemoryRAG
from src.vision.capture import ScreenCaptureEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("JarvisMain")


class JarvisAssistant:
    """Jarvis assistant system integrator."""

    def __init__(self) -> None:
        """Initialize Jarvis assistant modules."""
        logger.info("Initializing Jarvis Local Multimodal AI Assistant...")
        self.vision_engine = ScreenCaptureEngine()
        self.memory_rag = ContinuousMemoryRAG()
        self.stt_engine = SpeechToTextEngine()
        self.tts_engine = TextToSpeechEngine()
        self.vad_detector = VoiceActivityDetector()
        self.router = JarvisRouter(
            memory_rag=self.memory_rag,
            vision_engine=self.vision_engine,
        )
        logger.info("Jarvis modules loaded.")

    def start_background_services(self) -> None:
        """Start background workers (screen capture engine)."""
        self.vision_engine.start()

    def stop_background_services(self) -> None:
        """Stop background workers."""
        self.vision_engine.stop()

    def process_prompt(self, user_text: str) -> str:
        """
        Process user text prompt, stream response to TTS, and print output without duplicate execution.

        Args:
            user_text: Transcribed user query.

        Returns:
            Full assistant text response.
        """
        print(f"\n[Você]: {user_text}")
        print("[Jarvis]: ", end="", flush=True)

        start_time = time.perf_counter()

        def response_text_accumulator():
            # Generator that yields chunks from router while accumulating the full text
            for chunk in self.router.process_query_stream(user_text):
                print(chunk, end="", flush=True)
                full_text_chunks.append(chunk)
                yield chunk

        full_text_chunks = []
        # Single-pass execution through streaming TTS synthesizer
        for audio_chunk in self.tts_engine.stream_synthesize(response_text_accumulator()):
            pass

        print()  # Print newline after completed streaming response
        full_text = "".join(full_text_chunks)
        total_latency_ms = (time.perf_counter() - start_time) * 1000.0
        logger.info(f"Total processing latency: {total_latency_ms:.2f} ms")
        return full_text

    def run_cli_interactive(self) -> None:
        """Run interactive text CLI mode."""
        self.start_background_services()
        print("==========================================================")
        print(" Jarvis Assistant Ready (Modo CLI Interativo - pt-BR)")
        print(" Memória Contínua ativa no diretório Optane")
        print(" Digite 'sair' ou 'exit' para encerrar.")
        print("==========================================================")

        try:
            while True:
                user_input = input("\nDigite sua pergunta ou comando: ")
                if not user_input or user_input.strip() == "":
                    continue
                if user_input.strip().lower() in ["sair", "exit", "quit"]:
                    print("Encerrando Jarvis... Até logo!")
                    break
                self.process_prompt(user_input.strip())
        except KeyboardInterrupt:
            print("\nEncerrando Jarvis...")
        finally:
            self.stop_background_services()


def main() -> None:
    """Command-line interface entry point."""
    parser = argparse.ArgumentParser(description="Jarvis Local Multimodal AI Assistant")
    parser.add_argument("--cli", action="store_true", help="Run in CLI interactive mode")
    args = parser.parse_args()

    assistant = JarvisAssistant()
    assistant.run_cli_interactive()


if __name__ == "__main__":
    main()
