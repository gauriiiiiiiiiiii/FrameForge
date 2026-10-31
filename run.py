"""
FrameForge — one-command pipeline runner.
Usage:
    python run.py --topic "The fall of Tokyo" --auto
    python run.py --topic "Samurai story" --script scripts/samurai.txt
    python run.py --topic "Samurai story" --auto --music assets/bgm.mp3
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> None:
    print(f"\n>>> {' '.join(cmd)}\n")
    result = subprocess.run(cmd, check=True)


def main():
    parser = argparse.ArgumentParser(description="FrameForge pipeline")
    parser.add_argument("--topic", required=True, help="Video topic")
    parser.add_argument("--script", help="Path to script .txt (skip LLM script generation)")
    parser.add_argument("--auto", action="store_true", help="LLM generates the script")
    parser.add_argument("--music", help="Background music file")
    parser.add_argument("--skip-images", action="store_true", help="Skip image generation (use existing)")
    parser.add_argument("--skip-voice", action="store_true", help="Skip voice generation (use existing)")
    args = parser.parse_args()

    py = sys.executable

    # Stage 1: script → scenes
    stage1 = [py, "pipeline/script_to_scenes.py", "--topic", args.topic]
    if args.script:
        stage1 += ["--script", args.script]
    elif args.auto:
        stage1 += ["--auto"]
    run(stage1)

    # Stage 2: scenes → images
    if not args.skip_images:
        run([py, "pipeline/generate_images.py"])

    # Stage 3: scenes → voice
    if not args.skip_voice:
        run([py, "pipeline/generate_voice.py"])

    # Stage 4: assemble
    stage4 = [py, "pipeline/assemble_video.py"]
    if args.music:
        stage4 += ["--music", args.music]
    run(stage4)

    print("\nFrameForge pipeline complete. Video at output/video/final.mp4")


if __name__ == "__main__":
    main()
