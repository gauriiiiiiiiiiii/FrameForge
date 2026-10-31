"""
Stage 2: scene JSON → one image per scene via HuggingFace Inference API.
Usage:
    python pipeline/generate_images.py --scenes output/scenes/scenes.json
"""

import argparse
import json
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import HF_API_TOKEN, HF_IMAGE_MODEL, OUTPUT_DIR

ANIME_STYLE_SUFFIX = (
    ", anime style, detailed linework, cinematic lighting, "
    "vibrant colors, high detail, 16:9 aspect ratio"
)
NEGATIVE_PROMPT = (
    "text, watermark, blurry, low quality, western cartoon, "
    "deformed, ugly, bad anatomy"
)


def generate_image(prompt: str, out_path: Path, retries: int = 3) -> bool:
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"} if HF_API_TOKEN else {}
    url = f"https://api-inference.huggingface.co/models/{HF_IMAGE_MODEL}"
    payload = {
        "inputs": prompt + ANIME_STYLE_SUFFIX,
        "parameters": {"negative_prompt": NEGATIVE_PROMPT, "width": 1280, "height": 720},
    }

    for attempt in range(1, retries + 1):
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        if resp.status_code == 503:
            wait = 20 * attempt
            print(f"  Model loading, waiting {wait}s...")
            time.sleep(wait)
            continue
        if resp.status_code == 200:
            out_path.write_bytes(resp.content)
            return True
        print(f"  Error {resp.status_code}: {resp.text[:200]}")
        if attempt < retries:
            time.sleep(5)
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenes", default="output/scenes/scenes.json")
    parser.add_argument("--out-dir", default=f"{OUTPUT_DIR}/images")
    args = parser.parse_args()

    scenes = json.loads(Path(args.scenes).read_text())
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not HF_API_TOKEN:
        print(
            "WARNING: HF_API_TOKEN is empty. Free anonymous requests are rate-limited.\n"
            "Get a free token at https://huggingface.co/settings/tokens and set it in config/settings.py"
        )

    for scene in scenes:
        sid = scene["scene_id"]
        out_path = out_dir / f"scene_{sid:03d}.png"
        if out_path.exists():
            print(f"  scene {sid:03d}: already exists, skipping")
            continue
        print(f"  scene {sid:03d}: generating image...")
        ok = generate_image(scene["image_prompt"], out_path)
        status = "OK" if ok else "FAILED"
        print(f"  scene {sid:03d}: {status} → {out_path}")
        time.sleep(1)  # be polite to the free API

    print("Done.")


if __name__ == "__main__":
    main()
