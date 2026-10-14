# Jarvis Local Multimodal AI Assistant

**Jarvis** is an ultra-low latency, continuous local AI assistant written in native Python. It is optimized for sub-second voice-to-voice interaction, real-time desktop screen capture analysis, and lifelong continuous memory persisted directly on fast storage (e.g., Intel Optane drive or NVMe SSD).

---

## 🚀 Key Features

1. **Ultra-Low Latency Voice Pipeline (Target: 1.0 - 2.0s)**
   - **Speech-to-Text (STT):** Powered by `faster-whisper` (`whisper-large-v3-turbo` or INT8 quantized models) running on CUDA.
   - **Text-to-Speech (TTS):** Streaming, sentence-level synthesis via `kokoro-onnx` or `piper-tts` for instant time-to-first-audio playback.
   - **Voice Activity Detection (VAD):** Active speech segmentation using `silero-vad` or `webrtcvad`.

2. **Lifelong Continuous Memory Store (LanceDB RAG)**
   - **No Isolated Chat Sessions:** Single, continuous lifelong memory timeline.
   - All conversation turns, visual scene summaries (e.g. game character analysis, code reviews), timestamps, and tags are persisted in `LanceDB` on the fast storage drive.
   - Retrieve past events or visual references from weeks ago with fast vector similarity search.

3. **Fast Screen Capture Engine (Module A)**
   - Low-overhead desktop screen grabbing (<15ms target) using `mss` or `dxcam`.
   - Automatic frame downscaling (e.g. 1080p -> 720p) and atomic updates to the buffer path.
   - **Fast Vision Skip:** Automatically skips screen grabbing for standard text queries to minimize latency.

4. **Intel Optane & NVMe Storage Optimization**
   - Configured so that all models, HuggingFace/PyTorch caches, temporary frame buffers, and vector database tables reside directly on the fast Optane drive directory (e.g., `./data/optane/`).

5. **Portuguese (pt-BR) Native Support**
   - System prompts, STT language defaults, and TTS voice parameters are tailored for fluent Brazilian Portuguese interaction.

---

## 🛠️ Project Directory Layout

```text
jarvis-assistant/
├── .env.example            # Environment variables template
├── requirements.txt        # Core dependencies
├── config.py               # Fast storage path & model configuration
├── main.py                 # CLI & Voice assistant entry point
├── scripts/
│   └── benchmark.py        # Latency benchmark suite script
└── src/
    ├── __init__.py
    ├── audio/
    │   ├── __init__.py
    │   ├── stt.py          # faster-whisper STT integration
    │   ├── tts.py          # kokoro-onnx / piper-tts engine
    │   └── vad.py          # Silero VAD voice activity detector
    ├── core/
    │   ├── __init__.py
    │   └── router.py       # JarvisRouter orchestrator
    ├── memory/
    │   ├── __init__.py
    │   └── rag.py          # LanceDB continuous memory RAG
    └── vision/
        ├── __init__.py
        └── capture.py      # Low-overhead screen capture engine
```

---

## 📦 Setup & Installation

### 1. Prerequisites
- **Operating System:** Windows 10/11 or Linux.
- **Python:** Python 3.10+ (Python 3.12 recommended).
- **GPU:** NVIDIA GPU with 8 GB VRAM (CUDA 11.8 or 12.x installed).

### 2. Fast Storage Setup (Intel Optane / Fast SSD)
Place the project directory directly on your Intel Optane drive or high-speed NVMe mount path (e.g. `E:\jarvis-assistant` or `/mnt/optane/jarvis-assistant`).

### 3. Install Dependencies
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux:
source venv/bin/activate

pip install -r requirements.txt
```

---

## ⚙️ Configuration (`.env`)

Create a `.env` file in the root directory (or copy `.env.example`):

```ini
# Optane storage paths
OPTANE_STORAGE_PATH=./data/optane
VECTOR_DB_PATH=./data/optane/vector_db
BUFFER_PATH=./data/optane/buffer
MODELS_CACHE_PATH=./data/optane/models

# Target Language & Hardware Budget
TARGET_LANGUAGE=pt-BR
GPU_VRAM_BUDGET_GB=7.0

# Speech & Screen Capture Configuration
STT_MODEL_NAME=whisper-large-v3-turbo
STT_COMPUTE_TYPE=int8
TTS_ENGINE=kokoro-onnx
TTS_VOICE=pt_BR_1
CAPTURE_INTERVAL_SEC=2.0
CAPTURE_WIDTH=1280
CAPTURE_HEIGHT=720
```

---

## 🎮 Running Jarvis

### CLI Interactive Mode
To run Jarvis in CLI mode:
```bash
python main.py --cli
```

Example interaction:
```text
Digite sua pergunta ou comando: Qual o meu personagem favorito no jogo?
[Jarvis]: Lembro do seu personagem! Conforme registrei anteriormente: Meu personagem favorito no jogo é o Radahn.
```

---

## ⚡ Latency Benchmarking

To measure individual component latencies (Screen capture time, Optane Vector DB query speed, and End-to-End Voice Pipeline):

```bash
python scripts/benchmark.py
```

Sample Benchmark Output:
```text
==========================================================
 JARVIS LOCAL MULTIMODAL AI ASSISTANT - LATENCY BENCHMARK
==========================================================
1. Screen Capture Frame Latency : ~40.17 ms
2. Optane Vector DB Query Time  : ~10.27 ms
3. End-to-End Voice Pipeline    : ~270.34 ms (0.27s - well within 1.0 - 2.0s target)
==========================================================
```

---

## 📄 License
MIT License
