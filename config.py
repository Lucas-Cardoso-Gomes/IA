"""
Configuration management for Jarvis Local Multimodal AI Assistant.
All paths default to the Optane storage directory to maximize I/O throughput.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if available
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

# Fast Storage Paths (Intel Optane drive layout)
OPTANE_STORAGE_PATH = Path(os.getenv("OPTANE_STORAGE_PATH", BASE_DIR / "data" / "optane"))
VECTOR_DB_PATH = Path(os.getenv("VECTOR_DB_PATH", OPTANE_STORAGE_PATH / "vector_db"))
BUFFER_PATH = Path(os.getenv("BUFFER_PATH", OPTANE_STORAGE_PATH / "buffer"))
MODELS_CACHE_PATH = Path(os.getenv("MODELS_CACHE_PATH", OPTANE_STORAGE_PATH / "models"))

# Ensure essential Optane paths exist
for path in [OPTANE_STORAGE_PATH, VECTOR_DB_PATH, BUFFER_PATH, MODELS_CACHE_PATH]:
    path.mkdir(parents=True, exist_ok=True)

# Set HuggingFace / PyTorch cache env vars to Optane drive
os.environ["HF_HOME"] = str(MODELS_CACHE_PATH / "huggingface")
os.environ["TORCH_HOME"] = str(MODELS_CACHE_PATH / "torch")

# Language & System Settings
TARGET_LANGUAGE = os.getenv("TARGET_LANGUAGE", "pt-BR")
GPU_VRAM_BUDGET_GB = float(os.getenv("GPU_VRAM_BUDGET_GB", "7.0"))

# Module A: Screen Capture Engine
CAPTURE_INTERVAL_SEC = float(os.getenv("CAPTURE_INTERVAL_SEC", "2.0"))
CAPTURE_WIDTH = int(os.getenv("CAPTURE_WIDTH", "1280"))
CAPTURE_HEIGHT = int(os.getenv("CAPTURE_HEIGHT", "720"))
LATEST_FRAME_FILENAME = BUFFER_PATH / "latest_frame.jpg"

# Module B: Speech-to-Text (STT) & Text-to-Speech (TTS)
STT_MODEL_NAME = os.getenv("STT_MODEL_NAME", "whisper-large-v3-turbo")
STT_COMPUTE_TYPE = os.getenv("STT_COMPUTE_TYPE", "int8")  # int8, float16
TTS_ENGINE = os.getenv("TTS_ENGINE", "kokoro-onnx")        # kokoro-onnx, piper
TTS_VOICE = os.getenv("TTS_VOICE", "pt_BR_1")
VAD_THRESHOLD = float(os.getenv("VAD_THRESHOLD", "0.5"))

# Module C: Vector Database (Continuous Memory RAG)
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "3"))
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")

# Module D: Router & VLM
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "Qwen/Qwen2.5-VL-3B-Instruct")
LLM_QUANTIZATION = os.getenv("LLM_QUANTIZATION", "4bit")
