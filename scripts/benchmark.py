"""
Benchmark script for Jarvis Local Multimodal AI Assistant.
Measures latency performance for:
1. Screen capture time per frame (<15ms target).
2. Vector DB query latency on fast Optane storage path.
3. Full STT + Router/LLM + TTS pipeline end-to-end latency.
"""

import logging
import os
import sys
import time
import numpy as np

# Adjust python path to include repository root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import VECTOR_DB_PATH
from src.audio.stt import SpeechToTextEngine
from src.audio.tts import TextToSpeechEngine
from src.core.router import JarvisRouter
from src.memory.rag import ContinuousMemoryRAG
from src.vision.capture import ScreenCaptureEngine

logging.basicConfig(level=logging.ERROR)


def benchmark_screen_capture(iterations: int = 10) -> float:
    """Benchmark screen capture engine per frame time."""
    print("\n--- 1. Benchmarking Screen Capture Engine ---")
    engine = ScreenCaptureEngine()
    latencies = []

    for i in range(iterations):
        t0 = time.perf_counter()
        frame = engine.capture_frame()
        t1 = time.perf_counter()
        dur_ms = (t1 - t0) * 1000.0
        latencies.append(dur_ms)

    avg_ms = np.mean(latencies)
    min_ms = np.min(latencies)
    max_ms = np.max(latencies)
    print(f"Captured {iterations} frames (Resolution: {frame.size if frame else 'N/A'})")
    print(f"Average latency: {avg_ms:.2f} ms (Min: {min_ms:.2f} ms, Max: {max_ms:.2f} ms)")
    return avg_ms


def benchmark_vector_db_query(iterations: int = 10) -> float:
    """Benchmark vector database query latency on Optane storage path."""
    print("\n--- 2. Benchmarking Continuous Vector DB Query Latency ---")
    print(f"Vector DB storage location: {VECTOR_DB_PATH}")
    rag = ContinuousMemoryRAG()

    # Seed sample records if empty
    rag.add_memory("Análise do personagem Radahn no jogo de aventura", context_tags="gaming visual")
    rag.add_memory("Instruções de instalação de pacotes Python no servidor", context_tags="coding setup")

    latencies = []
    queries = [
        "Qual o nome do personagem do jogo?",
        "Como instalo os pacotes em python?",
        "O que falamos semana passada sobre o servidor?",
    ]

    for i in range(iterations):
        q = queries[i % len(queries)]
        t0 = time.perf_counter()
        results = rag.query_memory(q, top_k=3)
        t1 = time.perf_counter()
        dur_ms = (t1 - t0) * 1000.0
        latencies.append(dur_ms)

    avg_ms = np.mean(latencies)
    min_ms = np.min(latencies)
    max_ms = np.max(latencies)
    print(f"Executed {iterations} Vector DB queries.")
    print(f"Average query latency: {avg_ms:.2f} ms (Min: {min_ms:.2f} ms, Max: {max_ms:.2f} ms)")
    return avg_ms


def benchmark_full_pipeline() -> float:
    """Benchmark end-to-end STT + Router + TTS pipeline latency."""
    print("\n--- 3. Benchmarking End-to-End Pipeline (STT -> LLM/VLM -> TTS) ---")
    stt = SpeechToTextEngine()
    tts = TextToSpeechEngine()
    vision = ScreenCaptureEngine()
    rag = ContinuousMemoryRAG()
    router = JarvisRouter(memory_rag=rag, vision_engine=vision)

    # Simulated 16kHz audio input waveform (2 seconds)
    audio_sample = np.random.uniform(-0.1, 0.1, 32000).astype(np.float32)

    t_start = time.perf_counter()

    # Step 1: Speech-to-Text
    t0 = time.perf_counter()
    transcript = stt.transcribe(audio_sample, language="pt")
    if not transcript:
        transcript = "O que eu falei semana passada sobre o personagem do jogo?"
    stt_ms = (time.perf_counter() - t0) * 1000.0

    # Step 2: Router + LLM/VLM generation stream
    t1 = time.perf_counter()
    stream = router.process_query_stream(transcript)

    # Step 3: Sentence-level TTS audio synthesis
    t2 = time.perf_counter()
    audio_outputs = list(tts.stream_synthesize(stream))
    tts_ms = (time.perf_counter() - t2) * 1000.0

    total_pipeline_ms = (time.perf_counter() - t_start) * 1000.0

    print(f"Transcript input: '{transcript}'")
    print(f"Synthesized audio output segments: {len(audio_outputs)}")
    print(f"STT Latency: {stt_ms:.2f} ms")
    print(f"TTS Latency: {tts_ms:.2f} ms")
    print(f"TOTAL End-to-End Pipeline Latency: {total_pipeline_ms:.2f} ms ({total_pipeline_ms/1000.0:.3f} s)")
    return total_pipeline_ms


def run_all_benchmarks() -> None:
    """Run full benchmark suite."""
    print("==========================================================")
    print(" JARVIS LOCAL MULTIMODAL AI ASSISTANT - LATENCY BENCHMARK")
    print("==========================================================")
    cap_latency = benchmark_screen_capture()
    db_latency = benchmark_vector_db_query()
    pipeline_latency = benchmark_full_pipeline()

    print("\n==========================================================")
    print(" BENCHMARK SUMMARY")
    print("==========================================================")
    print(f"1. Screen Capture Frame Latency : {cap_latency:.2f} ms")
    print(f"2. Optane Vector DB Query Time  : {db_latency:.2f} ms")
    print(f"3. End-to-End Voice Pipeline    : {pipeline_latency:.2f} ms ({pipeline_latency/1000.0:.2f}s target: 1.0 - 2.0s)")
    print("==========================================================\n")


if __name__ == "__main__":
    run_all_benchmarks()
