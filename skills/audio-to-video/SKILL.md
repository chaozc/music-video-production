---
name: audio-to-video
description: Converts audio files into video files by combining them with images using ffmpeg. Use this skill whenever someone wants to turn a music track, podcast, or any audio into a video — including single audio + single image, or a playlist of multiple audio+image pairs concatenated into one video. Trigger on phrases like "make a video from my music", "combine audio and image into video", "create a YouTube video from my track", "make a playlist video", "audio to video", or any request to produce a video file from audio + image assets.
---

# Audio-to-Video Skill

Converts audio + image(s) into video using `ffmpeg`. Handles two modes:
- **Single**: one audio file + one image → one video
- **Playlist**: multiple audio+image pairs → one concatenated video (each song gets its own image, all joined into a single output file)

## Prerequisites

- `ffmpeg` must be installed and available on PATH
- `python3` for the build script
- `Pillow` (optional, only if using text overlay): `pip install Pillow`

Install ffmpeg:
- **macOS**: `brew install ffmpeg`
- **Linux (Debian/Ubuntu)**: `sudo apt install ffmpeg`
- **Linux (Fedora/RHEL)**: `sudo dnf install ffmpeg`

Verify with: `ffmpeg -version`

## Build Script

This skill includes `scripts/build-video.py` — a CLI tool that wraps ffmpeg with correct flags for audio-to-video conversion. **Prefer using the script over raw ffmpeg commands** for reliability and consistency.

The script is at `scripts/build-video.py` within this skill directory.

```bash
# Single track
python build-video.py --audio track.mp3 --cover cover.png --output video.mp4

# Playlist from directory
python build-video.py --mp3-dir ./songs --cover cover.png --output playlist.mp4

# Playlist with explicit track order
python build-video.py --mp3-dir ./songs \
  --order "Track-A.mp3,Track-B.mp3,Track-C.mp3" \
  --cover cover.png --output playlist.mp4

# With text overlay on cover
python build-video.py --mp3-dir ./songs --cover cover.png \
  --title "Album Title" --subtitle "by Artist" --font /path/to/font.ttf \
  --output playlist.mp4

# Custom resolution + save timestamps
python build-video.py --mp3-dir ./songs --cover cover.png \
  --resolution 3840x2160 --timestamps-file timestamps.json --output playlist.mp4
```

The script handles: encoding flags, resolution scaling/padding, segment concatenation, temp file cleanup, and timestamp generation. The agent decides creative parameters (track order, title text, etc.) and passes them as CLI arguments.

## Workflow

### Step 1 — Gather inputs

Ask the user (or infer from context) for:
- **Mode**: single or playlist
- **Audio file(s)**: path(s) to `.mp3`, `.wav`, `.flac`, `.aac`, `.m4a`, or similar
- **Image file(s)**: path(s) to `.jpg`, `.png`, or `.webp` — one per audio in playlist mode
- **Output path**: where to save the final video (default: same directory as the first audio file)
- **Output format**: if the user specifies a format or the output path has an extension, honour it. Otherwise use this heuristic:
  - Uploading to YouTube or sharing online → `mp4`
  - Staying on macOS / going into Final Cut Pro or iMovie → `mov`
  - No clear signal → default to `mp4` and mention the user can request `mov` instead
- **Video resolution**: default `1920x1080`. Common alternatives: `3840x2160` (4K), `1080x1080` (square/Instagram)

If anything is ambiguous, ask before running. Never guess file paths.

### Step 2 — Validate inputs

Before running ffmpeg:
- Confirm all input files exist
- Confirm image and audio counts match in playlist mode
- Warn if output file already exists and ask before overwriting

### Step 3 — Build and run the ffmpeg command

#### Single mode

```bash
ffmpeg -loop 1 -i "image.jpg" -i "audio.mp3" \
  -c:v libx264 -tune stillimage -c:a aac -b:a 192k \
  -pix_fmt yuv420p -shortest \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black" \
  "output.mp4"
```

Key flags explained:
- `-loop 1`: loops the static image for the duration of the audio
- `-shortest`: ends the video when the audio ends
- `-tune stillimage`: optimizes H.264 encoding for a static image source
- `-pix_fmt yuv420p`: ensures broad compatibility (required for YouTube)
- `scale=...,pad=...`: letterboxes/pillarboxes the image to fill the target resolution without cropping

#### Playlist mode

Playlist mode requires two steps: encode each segment individually, then concatenate.

**Step A — Encode each segment:**

For each audio+image pair, run the single-mode command above, outputting to a temp file:

```bash
ffmpeg -loop 1 -i "image1.jpg" -i "audio1.mp3" \
  -c:v libx264 -tune stillimage -c:a aac -b:a 192k \
  -pix_fmt yuv420p -shortest \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black" \
  "/tmp/segment_01.mp4"
```

Repeat for all pairs, naming segments `segment_01.mp4`, `segment_02.mp4`, etc.

**Step B — Write a concat list file:**

```
# concat_list.txt
file '/tmp/segment_01.mp4'
file '/tmp/segment_02.mp4'
file '/tmp/segment_03.mp4'
```

**Step C — Concatenate:**

```bash
ffmpeg -f concat -safe 0 -i concat_list.txt \
  -c copy \
  "playlist_output.mp4"
```

`-c copy` avoids re-encoding, so this step is fast regardless of playlist length.

**Step D — Clean up temp files** after a successful concat:

```bash
rm /tmp/segment_*.mp4 concat_list.txt
```

### Step 4 — Report results

After ffmpeg completes:
- Confirm the output file exists and report its size
- Report the video duration (use `ffprobe` if available: `ffprobe -v quiet -show_entries format=duration -of csv=p=0 output.mp4`)
- If ffmpeg exited with an error, show the relevant portion of stderr and suggest a fix

## Format notes

| Format | Best for | ffmpeg flags |
|--------|----------|--------------|
| `mp4` | YouTube, general sharing, default | `-c:v libx264 -c:a aac` |
| `mov` | macOS editing (Final Cut, iMovie) | Same codec flags as mp4, just change extension |
| `webm` | Web embedding | `-c:v libvpx-vp9 -c:a libopus` — slower to encode, mention this |

For `mp4` and `mov`, always include `-pix_fmt yuv420p` for maximum compatibility.
For `mov` on macOS, you may alternatively use `-c:v h264_videotoolbox` for hardware-accelerated encoding (significantly faster on Apple Silicon), but it is not available on Linux — only suggest this if the user is on macOS.

## Resolution notes

- Always apply the `scale + pad` filter so any image aspect ratio is safely letterboxed/pillarboxed. Never crop or stretch.
- For square images (album art), `1920x1080` output will result in pillarboxes on the sides. Consider offering `1080x1080` output for Instagram/square use cases.
- 4K (`3840x2160`) is supported but encodes significantly slower on CPU. Mention this to the user if they request it.

## Error handling

| Error | Likely cause | Fix |
|-------|-------------|-----|
| `No such file or directory` | Wrong path | Confirm file exists; check spaces in path (quote the path) |
| `Invalid data found` | Corrupt or unsupported audio format | Try converting audio first: `ffmpeg -i input.xxx -c:a aac temp.aac` |
| `codec not found` | ffmpeg built without that codec | Install a full build: `brew install ffmpeg` (macOS) or use a static build |
| `Conversion failed` on concat | Mismatched codecs between segments | Re-encode all segments with the same flags before concatenating |

## Future: additional modes (not yet implemented)

- **Slideshow**: single audio + multiple images, each shown for equal or specified durations
- **Beat-synced**: detect BPM and cut between images on the beat (requires audio analysis)
- **Subtitle overlay**: burn in lyrics or chapter markers as text (requires `.srt` or timed text file)
