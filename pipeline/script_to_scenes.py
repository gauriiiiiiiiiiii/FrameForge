"""
Stage 1: script text → scene JSON via Ollama (local LLM, CPU).
Usage:
    python pipeline/script_to_scenes.py --topic "The Last Samurai" --script scripts/samurai.txt
    python pipeline/script_to_scenes.py --topic "My Topic" --auto   # LLM writes script too
"""

import argparse
import json
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import OLLAMA_BASE_URL, OLLAMA_MODEL

SYSTEM_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "scene_system.txt"


def ollama_chat(system: str, user: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
    }
    resp = requests.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload, timeout=300)
    resp.raise_for_status()
    return resp.json()["message"]["content"]


def generate_script(topic: str) -> str:
    system = (
        "You are a YouTube scriptwriter. Write a 60-second narrated script (about 150 words) "
        "for an anime-inspired video. No stage directions. Pure spoken narration only."
    )
    return ollama_chat(system, f"Topic: {topic}")


def script_to_scenes(topic: str, script: str) -> list[dict]:
    system = SYSTEM_PROMPT_PATH.read_text()
    user = f"Topic: {topic}\n\nScript:\n{script}"
    raw = ollama_chat(system, user)
    # Strip accidental markdown fences
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", required=True)
    parser.add_argument("--script", help="Path to a .txt script file")
    parser.add_argument("--auto", action="store_true", help="LLM writes the script")
    parser.add_argument("--out", default="output/scenes/scenes.json")
    args = parser.parse_args()

    if args.auto or not args.script:
        print(f"[1/2] Generating script for: {args.topic}")
        script = generate_script(args.topic)
        print(script[:200], "...\n")
    else:
        script = Path(args.script).read_text()

    print("[2/2] Generating scene JSON...")
    scenes = script_to_scenes(args.topic, script)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(scenes, indent=2, ensure_ascii=False))
    print(f"Wrote {len(scenes)} scenes → {out}")


if __name__ == "__main__":
    main()
