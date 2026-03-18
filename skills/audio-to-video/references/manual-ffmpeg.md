# Manual ffmpeg Commands

Fallback reference when `scripts/build-video.py` is not available. Prefer the script for consistency.

## Single Mode

```bash
ffmpeg -loop 1 -i "image.jpg" -i "audio.mp3" \
  -c:v libx264 -tune stillimage -c:a aac -b:a 192k \
  -pix_fmt yuv420p -shortest \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black" \
  "output.mp4"
```

Key flags:
- `-loop 1`: loops the static image for the duration of the audio
- `-shortest`: ends the video when the audio ends
- `-tune stillimage`: optimizes H.264 encoding for a static image source
- `-pix_fmt yuv420p`: ensures broad compatibility (required for YouTube)
- `scale=...,pad=...`: letterboxes/pillarboxes the image to fill the target resolution without cropping

## Playlist Mode

### Step A — Encode each segment

For each audio+image pair:

```bash
ffmpeg -loop 1 -i "image1.jpg" -i "audio1.mp3" \
  -c:v libx264 -tune stillimage -c:a aac -b:a 192k \
  -pix_fmt yuv420p -shortest \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black" \
  "/tmp/segment_01.mp4"
```

### Step B — Write concat list

```
file '/tmp/segment_01.mp4'
file '/tmp/segment_02.mp4'
file '/tmp/segment_03.mp4'
```

### Step C — Concatenate

```bash
ffmpeg -f concat -safe 0 -i concat_list.txt -c copy "playlist_output.mp4"
```

### Step D — Clean up

```bash
rm /tmp/segment_*.mp4 concat_list.txt
```

## Format Notes

| Format | Best for | ffmpeg flags |
|--------|----------|--------------|
| `mp4` | YouTube, general sharing, default | `-c:v libx264 -c:a aac` |
| `mov` | macOS editing (Final Cut, iMovie) | Same codec flags, just change extension |
| `webm` | Web embedding | `-c:v libvpx-vp9 -c:a libopus` (slower) |

- Always include `-pix_fmt yuv420p` for mp4/mov
- On macOS, `-c:v h264_videotoolbox` enables hardware-accelerated encoding (Apple Silicon only)

## Resolution Notes

- Always apply `scale + pad` filter — never crop or stretch
- Square images on 1920x1080 → pillarboxes. Offer `1080x1080` for Instagram
- 4K (`3840x2160`) encodes significantly slower on CPU
