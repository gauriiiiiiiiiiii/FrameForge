"""
Stage 3: scene JSON → one .mp3 per scene via edge-tts (default) or Kokoro.
Usage:
    python pipeline/generate_voice.py --scenes output/scenes/scenes.json
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import EDGE_TTS_VOICE, OUTPUT_DIR, TTS_ENGINE


async def generate_edge_tts(text: str, out_path: Path, voice: str) -> None:
    try:
        import edge_tts
    except ImportError:
        print("edge-tts not installed. Run: pip install edge-tts")
        raise

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(out_path))


def generate_kokoro(text: str, out_path: Path, model_path: str) -> None:
    try:
        from kokoro import KPipeline
        import soundfile as sf
    except ImportError:
        print("Kokoro not installed. See https://github.com/hexgrad/kokoro")
        raise

    pipeline = KPipeline(lang_code="a")
    generator = pipeline(text, voice="af_heart", speed=1.0)
    for _, _, audio in generator:
        sf.write(str(out_path), audio, 24000)
        break  # one chunk per scene line is enough


def get_audio_duration_ms(path: Path) -> int:
    try:
        from mutagen.mp3 import MP3
        return int(MP3(str(path)).info.length * 1000)
    except Exception:
        return 4000  # fallback: assume 4s


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenes", default="output/scenes/scenes.json")
    parser.add_argument("--out-dir", default=f"{OUTPUT_DIR}/audio")
    args = parser.parse_args()

    scenes = json.loads(Path(args.scenes).read_text())
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for scene in scenes:
        sid = scene["scene_id"]
        text = scene["narration"]
        ext = "mp3" if TTS_ENGINE == "edge" else "wav"
        out_path = out_dir / f"scene_{sid:03d}.{ext}"

        if out_path.exists():
            print(f"  scene {sid:03d}: already exists, skipping")
            continue

        print(f"  scene {sid:03d}: generating voice ({TTS_ENGINE})...")
        if TTS_ENGINE == "edge":
            asyncio.run(generate_edge_tts(text, out_path, EDGE_TTS_VOICE))
        else:
            from config.settings import KOKORO_MODEL_PATH
            generate_kokoro(text, out_path, KOKORO_MODEL_PATH)

        duration_ms = get_audio_duration_ms(out_path)
        scene["audio_path"] = str(out_path)
        scene["audio_duration_ms"] = duration_ms
        print(f"  scene {sid:03d}: OK ({duration_ms}ms) → {out_path}")

    # Write back enriched scenes (with audio paths and durations)
    enriched_path = Path(args.scenes).with_stem("scenes_with_audio")
    enriched_path.write_text(json.dumps(scenes, indent=2, ensure_ascii=False))
    print(f"\nWrote enriched scenes → {enriched_path}")


if __name__ == "__main__":
    main()
