"""
FrameForge configuration.
Edit this file before running the pipeline.
"""

# --- LLM (Ollama, runs locally on CPU) ---
OLLAMA_MODEL = "llama3.2"          # or mistral, phi3 — whatever you have pulled
OLLAMA_BASE_URL = "http://localhost:11434"

# --- Image generation ---
# Option A: Hugging Face free Inference API (no GPU needed on your side)
HF_API_TOKEN = ""                  # https://huggingface.co/settings/tokens (free read token)
HF_IMAGE_MODEL = "black-forest-labs/FLUX.1-schnell"

# --- TTS ---
# "edge" uses Microsoft Edge voices via edge-tts (free, needs internet, no key)
# "kokoro" uses the local Kokoro model (fully offline after download)
TTS_ENGINE = "edge"
EDGE_TTS_VOICE = "en-US-AnaMelNeural"   # Anime-sounding voice
KOKORO_MODEL_PATH = "./models/kokoro"    # only used when TTS_ENGINE="kokoro"

# --- Video ---
VIDEO_FPS = 24
VIDEO_RESOLUTION = (1920, 1080)      # 1080p horizontal
SCENE_DEFAULT_DURATION = 5           # seconds when not set in scene JSON
AUDIO_PADDING_MS = 200               # silence added after each line

# --- Output ---
OUTPUT_DIR = "./output"
