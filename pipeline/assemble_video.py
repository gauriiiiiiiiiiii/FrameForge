"""
Stage 4: images + audio → final video via MoviePy + FFmpeg.
Applies motion effects (zoom, pan, parallax) to still images.
Usage:
    python pipeline/assemble_video.py --scenes output/scenes/scenes_with_audio.json
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from moviepy import (
    AudioFileClip,
    CompositeVideoClip,
    ImageClip,
    VideoFileClip,
    concatenate_videoclips,
)
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import (
    AUDIO_PADDING_MS,
    OUTPUT_DIR,
    SCENE_DEFAULT_DURATION,
    VIDEO_FPS,
    VIDEO_RESOLUTION,
)

W, H = VIDEO_RESOLUTION


def load_image_resized(path: Path) -> np.ndarray:
    img = Image.open(path).convert("RGB")
    # Scale to fill 1920×1080, crop center
    img_ratio = img.width / img.height
    target_ratio = W / H
    if img_ratio > target_ratio:
        new_h = H
        new_w = int(H * img_ratio)
    else:
        new_w = W
        new_h = int(W / img_ratio)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - W) // 2
    top = (new_h - H) // 2
    img = img.crop((left, top, left + W, top + H))
    return np.array(img)


def make_motion_clip(img_path: Path, duration: float, motion: str) -> ImageClip:
    arr = load_image_resized(img_path)
    clip = ImageClip(arr, duration=duration)

    if motion == "static":
        return clip.with_fps(VIDEO_FPS)

    # Zoom / pan via a resize + position function
    scale_start, scale_end = 1.0, 1.0
    pan_x_start, pan_x_end = 0, 0

    if motion == "zoom_in":
        scale_start, scale_end = 1.0, 1.15
    elif motion == "zoom_out":
        scale_start, scale_end = 1.15, 1.0
    elif motion == "pan_left":
        scale_start = scale_end = 1.1
        pan_x_start, pan_x_end = int(0.05 * W), -int(0.05 * W)
    elif motion == "pan_right":
        scale_start = scale_end = 1.1
        pan_x_start, pan_x_end = -int(0.05 * W), int(0.05 * W)
    elif motion == "parallax":
        scale_start, scale_end = 1.08, 1.0
        pan_x_start, pan_x_end = int(0.03 * W), 0

    def make_frame(get_frame, t):
        progress = t / duration
        scale = scale_start + (scale_end - scale_start) * progress
        px = int(pan_x_start + (pan_x_end - pan_x_start) * progress)
        frame = get_frame(t)
        h_f, w_f = frame.shape[:2]
        new_w = int(w_f * scale)
        new_h = int(h_f * scale)
        resized = np.array(Image.fromarray(frame).resize((new_w, new_h), Image.LANCZOS))
        x0 = max(0, (new_w - W) // 2 + px)
        y0 = max(0, (new_h - H) // 2)
        return resized[y0 : y0 + H, x0 : x0 + W]

    from moviepy import VideoClip
    return VideoClip(lambda t: make_frame(clip.get_frame, t), duration=duration).with_fps(VIDEO_FPS)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenes", default="output/scenes/scenes_with_audio.json")
    parser.add_argument("--out", default=f"{OUTPUT_DIR}/video/final.mp4")
    parser.add_argument("--music", help="Optional background music .mp3")
    args = parser.parse_args()

    scenes = json.loads(Path(args.scenes).read_text())
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    clips = []
    for scene in scenes:
        sid = scene["scene_id"]
        img_path = Path(f"{OUTPUT_DIR}/images/scene_{sid:03d}.png")
        audio_path = scene.get("audio_path")

        if not img_path.exists():
            print(f"  scene {sid:03d}: image missing, skipping")
            continue

        # Duration: audio length + padding, or fallback to default
        if audio_path and Path(audio_path).exists():
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration + AUDIO_PADDING_MS / 1000
        else:
            audio_clip = None
            duration = scene.get("duration_hint", SCENE_DEFAULT_DURATION)

        motion = scene.get("motion_type", "zoom_in")
        print(f"  scene {sid:03d}: {motion}, {duration:.1f}s")
        video_clip = make_motion_clip(img_path, duration, motion)

        if audio_clip:
            video_clip = video_clip.with_audio(audio_clip)

        clips.append(video_clip)

    if not clips:
        print("No clips to assemble.")
        return

    final = concatenate_videoclips(clips, method="compose")

    print(f"\nRendering {final.duration:.1f}s video → {out_path}")
    final.write_videofile(
        str(out_path),
        fps=VIDEO_FPS,
        codec="libx264",
        audio_codec="aac",
        threads=4,
        preset="fast",
    )
    print("Done.")


if __name__ == "__main__":
    main()
