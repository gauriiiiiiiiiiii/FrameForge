# FrameForge

Anime-inspired AI YouTube video pipeline. Local-first, free to run.

## Stack

| Stage | Tool | Cost |
|-------|------|------|
| Script + scene JSON | Ollama (local LLM) | Free |
| Images | HuggingFace Inference API | Free (rate-limited) |
| Voice | edge-tts or Kokoro | Free |
| Assembly | MoviePy + FFmpeg | Free |

## Setup

### 1. Prerequisites

```bash
# Python 3.11+
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# FFmpeg (required by MoviePy)
brew install ffmpeg          # macOS
# sudo apt install ffmpeg    # Ubuntu

# Ollama (local LLM)
brew install ollama
ollama pull llama3.2         # ~2 GB, runs on CPU
```

### 2. HuggingFace token (free)

1. Go to https://huggingface.co/settings/tokens
2. Create a **read** token (free)
3. Set it in `config/settings.py` → `HF_API_TOKEN`

### 3. Run

```bash
# Auto-generate script and video for a topic
python run.py --topic "The Last Samurai" --auto

# Supply your own script
python run.py --topic "My Story" --script scripts/my_story.txt

# Add background music
python run.py --topic "Epic Battle" --auto --music assets/bgm.mp3

# Resume (skip stages already done)
python run.py --topic "My Story" --auto --skip-images --skip-voice
```

Output: `output/video/final.mp4`

## Individual stages

```bash
python pipeline/script_to_scenes.py --topic "Topic" --auto
python pipeline/generate_images.py
python pipeline/generate_voice.py
python pipeline/assemble_video.py
```

## Cost

- **Fully free** with this setup.
- HuggingFace free tier: ~1000 requests/month, may queue for cold-start.
- Get a paid HF Inference tier (~$9/month) for faster generation.

## Switching TTS

Edit `config/settings.py`:
- `TTS_ENGINE = "edge"` — Microsoft Edge voices, free, needs internet
- `TTS_ENGINE = "kokoro"` — fully offline, install separately: `pip install kokoro soundfile`
