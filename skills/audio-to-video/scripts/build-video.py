#!/usr/bin/env python3
"""
Build a video from audio file(s) + a cover image using ffmpeg.

Modes:
  Single:   one audio + one image → one video
  Playlist: multiple audio files + one image → concatenated video with timestamps

Usage:
  # Single track
  python build-video.py --audio track.mp3 --cover cover.png --output video.mp4

  # Playlist (directory of MP3s)
  python build-video.py --mp3-dir ./songs --cover cover.png --output playlist.mp4

  # Playlist with explicit order
  python build-video.py --mp3-dir ./songs --order "Track-A.mp3,Track-B.mp3,Track-C.mp3" \
    --cover cover.png --output playlist.mp4

  # Custom resolution
  python build-video.py --audio track.mp3 --cover cover.png --resolution 3840x2160 --output video.mp4

  # Text overlay on cover
  python build-video.py --mp3-dir ./songs --cover cover.png \
    --title "My Album" --subtitle "by Artist" --font /path/to/font.ttf --output video.mp4
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

def parse_args():
    p = argparse.ArgumentParser(description="Build video from audio + cover image")

    # Input — either single audio or directory
    input_group = p.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--audio", help="Single audio file path")
    input_group.add_argument("--mp3-dir", help="Directory containing audio files")

    p.add_argument("--cover", required=True, help="Cover image path (jpg/png/webp)")
    p.add_argument("--output", required=True, help="Output video path")
    p.add_argument("--order", help="Comma-separated filenames for playlist order (only with --mp3-dir)")
    p.add_argument("--resolution", default="1920x1080", help="Video resolution WxH (default: 1920x1080)")
    p.add_argument("--audio-bitrate", default="192k", help="Audio bitrate (default: 192k)")

    # Optional text overlay
    p.add_argument("--title", help="Title text to overlay on cover")
    p.add_argument("--subtitle", help="Subtitle text to overlay on cover")
    p.add_argument("--font", help="Path to .ttf font for text overlay (required if --title is used)")

    # Output options
    p.add_argument("--timestamps-file", help="Write timestamps JSON to this path")

    return p.parse_args()


def get_duration(filepath):
    """Get audio duration in seconds via ffprobe."""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", filepath],
        capture_output=True, text=True
    )
    return float(result.stdout.strip())


def add_text_overlay(cover_path, title, subtitle, font_path, output_path):
    """Add title/subtitle text overlay to cover image using Pillow."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("ERROR: Pillow is required for text overlay. Install with: pip install Pillow", file=sys.stderr)
        sys.exit(1)

    img = Image.open(cover_path).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    w, h = img.size

    title_font = ImageFont.truetype(font_path, int(h * 0.08))
    elements = []

    # Measure title
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_w = title_bbox[2] - title_bbox[0]
    title_h = title_bbox[3] - title_bbox[1]
    elements.append(("title", title, title_font, title_w, title_h))

    # Measure subtitle if provided
    if subtitle:
        sub_font = ImageFont.truetype(font_path, int(h * 0.035))
        sub_bbox = draw.textbbox((0, 0), subtitle, font=sub_font)
        sub_w = sub_bbox[2] - sub_bbox[0]
        sub_h = sub_bbox[3] - sub_bbox[1]
        elements.append(("subtitle", subtitle, sub_font, sub_w, sub_h))

    # Calculate vertical position (bottom area)
    total_text_h = sum(el[4] for el in elements) + int(h * 0.03) * (len(elements) - 1)
    start_y = int(h * 0.78)

    # Semi-transparent dark band
    band_y1 = start_y - int(h * 0.03)
    band_y2 = start_y + total_text_h + int(h * 0.04)
    draw.rectangle([(0, band_y1), (w, band_y2)], fill=(0, 0, 0, 100))

    # Draw text
    y = start_y
    for _, text, font, tw, th in elements:
        x = (w - tw) // 2
        draw.text((x + 2, y + 2), text, font=font, fill=(0, 0, 0, 120))  # shadow
        draw.text((x, y), text, font=font, fill=(255, 255, 255, 240))
        y += th + int(h * 0.03)

    result = Image.alpha_composite(img, overlay)
    result.convert("RGB").save(output_path, quality=95)
    print(f"✅ Cover with text overlay: {output_path}")


def get_audio_files(mp3_dir, order=None):
    """Get list of audio files from directory, optionally ordered."""
    audio_exts = {".mp3", ".wav", ".flac", ".aac", ".m4a", ".ogg"}
    all_files = [f for f in os.listdir(mp3_dir) if os.path.splitext(f)[1].lower() in audio_exts]

    if order:
        ordered_names = [n.strip() for n in order.split(",")]
        ordered = []
        remaining = list(all_files)
        for name in ordered_names:
            if name in remaining:
                ordered.append(name)
                remaining.remove(name)
            else:
                print(f"⚠️  Ordered file not found, skipping: {name}", file=sys.stderr)
        # Append any remaining files not in the order list
        ordered.extend(sorted(remaining))
        return ordered
    else:
        return sorted(all_files)


def format_timestamp(seconds):
    """Format seconds to MM:SS or H:MM:SS."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def build_single(audio_path, cover_path, output_path, resolution, audio_bitrate):
    """Build video from single audio + cover image."""
    w, h = resolution.split("x")
    print(f"🎬 Building video: {audio_path}")

    subprocess.run([
        "ffmpeg", "-y",
        "-loop", "1", "-i", cover_path,
        "-i", audio_path,
        "-c:v", "libx264", "-tune", "stillimage",
        "-c:a", "aac", "-b:a", audio_bitrate,
        "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black",
        "-pix_fmt", "yuv420p",
        "-shortest",
        output_path
    ], check=True)

    size_mb = os.path.getsize(output_path) / 1024 / 1024
    duration = get_duration(output_path)
    print(f"✅ {output_path} ({size_mb:.1f} MB, {format_timestamp(duration)})")


def build_playlist(mp3_dir, audio_files, cover_path, output_path, resolution, audio_bitrate):
    """Build concatenated video from multiple audio files + one cover image."""
    w, h = resolution.split("x")
    timestamps = []
    current_time = 0
    tmp_dir = tempfile.mkdtemp(prefix="build-video-")

    print(f"🎵 Playlist: {len(audio_files)} tracks\n")

    # Step 1: Encode each segment
    segment_paths = []
    for i, filename in enumerate(audio_files):
        audio_path = os.path.join(mp3_dir, filename)
        duration = get_duration(audio_path)
        title = os.path.splitext(filename)[0].replace("-", " ").replace("_", " ")

        ts = format_timestamp(current_time)
        timestamps.append({"timestamp": ts, "title": title, "seconds": current_time})
        print(f"  {ts}  {title} ({duration:.0f}s)")

        segment_path = os.path.join(tmp_dir, f"segment_{i:03d}.mp4")
        subprocess.run([
            "ffmpeg", "-y",
            "-loop", "1", "-i", cover_path,
            "-i", audio_path,
            "-c:v", "libx264", "-tune", "stillimage",
            "-c:a", "aac", "-b:a", audio_bitrate,
            "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black",
            "-pix_fmt", "yuv420p",
            "-shortest",
            segment_path
        ], check=True, capture_output=True)

        segment_paths.append(segment_path)
        current_time += duration

    print(f"\n📊 Total duration: {format_timestamp(current_time)}")

    # Step 2: Concatenate
    concat_file = os.path.join(tmp_dir, "concat.txt")
    with open(concat_file, "w") as f:
        for sp in segment_paths:
            f.write(f"file '{sp}'\n")

    print("🔗 Concatenating...")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file,
        "-c", "copy", output_path
    ], check=True, capture_output=True)

    # Cleanup temp files
    for sp in segment_paths:
        os.remove(sp)
    os.remove(concat_file)
    os.rmdir(tmp_dir)

    size_mb = os.path.getsize(output_path) / 1024 / 1024
    print(f"✅ {output_path} ({size_mb:.1f} MB)")

    return timestamps


def main():
    args = parse_args()

    # Validate inputs
    if not os.path.exists(args.cover):
        print(f"ERROR: Cover image not found: {args.cover}", file=sys.stderr)
        sys.exit(1)

    if args.audio and not os.path.exists(args.audio):
        print(f"ERROR: Audio file not found: {args.audio}", file=sys.stderr)
        sys.exit(1)

    if args.mp3_dir and not os.path.isdir(args.mp3_dir):
        print(f"ERROR: Audio directory not found: {args.mp3_dir}", file=sys.stderr)
        sys.exit(1)

    if args.title and not args.font:
        print("ERROR: --font is required when using --title", file=sys.stderr)
        sys.exit(1)

    # Text overlay
    cover_to_use = args.cover
    if args.title:
        cover_to_use = os.path.join(os.path.dirname(args.output), "_cover-with-text.png")
        add_text_overlay(args.cover, args.title, args.subtitle, args.font, cover_to_use)

    # Build
    if args.audio:
        build_single(args.audio, cover_to_use, args.output, args.resolution, args.audio_bitrate)
    else:
        audio_files = get_audio_files(args.mp3_dir, args.order)
        if not audio_files:
            print("ERROR: No audio files found in directory", file=sys.stderr)
            sys.exit(1)

        timestamps = build_playlist(
            args.mp3_dir, audio_files, cover_to_use, args.output,
            args.resolution, args.audio_bitrate
        )

        # Save timestamps
        if args.timestamps_file:
            with open(args.timestamps_file, "w") as f:
                json.dump(timestamps, f, indent=2, ensure_ascii=False)
            print(f"📝 Timestamps: {args.timestamps_file}")
        else:
            # Print timestamps to stdout for agent to capture
            print("\n📋 Timestamps:")
            for t in timestamps:
                print(f"  {t['timestamp']} {t['title']}")

    # Cleanup text overlay temp file
    if args.title and cover_to_use != args.cover and os.path.exists(cover_to_use):
        os.remove(cover_to_use)


if __name__ == "__main__":
    main()
