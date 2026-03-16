---
name: youtube-upload
description: Upload videos to YouTube with auto-generated titles, descriptions, tags, and thumbnails. Use when someone wants to publish a video to YouTube, upload content, or set up a YouTube release. Triggers on phrases like "upload to YouTube", "publish video", "post to YouTube", "release on YouTube", "set up YouTube upload". Handles metadata generation, thumbnail selection, scheduling, and playlist management.
---

# YouTube Upload

Upload videos to YouTube via the YouTube Data API v3. Auto-generates metadata (title, description, tags) from music/video context.

## Prerequisites

- Python 3.10+
- Google API OAuth2 credentials with YouTube Data API v3 enabled
- `google-api-python-client` and `google-auth-oauthlib` packages

### Setup

1. Create a project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable **YouTube Data API v3**
3. Create **OAuth 2.0 Client ID** (Desktop app type)
4. Download `client_secrets.json`
5. Set environment variable: `YOUTUBE_CLIENT_SECRETS=/path/to/client_secrets.json`
6. First run will open browser for OAuth consent — grants token stored at `~/.youtube-upload-token.json`

See [references/setup.md](references/setup.md) for detailed setup guide.

## Workflow

### 1. Gather parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| video-file | yes | — | Path to video file (.mp4, .mov, .webm) |
| title | no | auto-generated | Video title |
| description | no | auto-generated | Video description |
| tags | no | auto-generated | Comma-separated tags |
| category | no | `10` (Music) | YouTube category ID |
| privacy | no | `private` | `public`, `unlisted`, or `private` |
| thumbnail | no | — | Path to thumbnail image |
| playlist | no | — | Playlist name or ID to add video to |
| schedule | no | — | ISO 8601 datetime for scheduled publish |
| language | no | `en` | Video language |

### 2. Auto-generate metadata

When title, description, or tags are not provided, generate them from context:

**From metadata sidecar** (if available from upstream skills):
- Read the music-generation or cover-art-generation JSON sidecar
- Derive title from mood + genre (e.g., "Cozy Bedtime Jazz | Relaxing Piano & Guitar")
- Derive description from prompt and style
- Derive tags from genre, mood, and style keywords

**Title format patterns:**
```
<Mood> <Genre> | <Instruments/Vibe>
<Genre> for <Activity> | <Mood> <Instrument>
<Adjective> <Genre> · <Setting/Time>
```

Examples:
```
Mellow Bedtime Jazz | Piano & Acoustic Guitar, Slow Waltz
Cozy French Jazz for Sleep | Soft Female Vocals
Rainy Evening Jazz · Café Piano Ambience
```

**Description template:**
```
<mood description>

🎵 Perfect for: <activities>
🎹 Instruments: <instruments>
☕ Mood: <mood>

<hashtags>

Enjoy this <genre> track and don't forget to subscribe for more relaxing music!
```

**Tags:** Extract from genre, mood, instruments, activities. Example:
```
jazz, cozy jazz, bedtime jazz, relaxing piano, acoustic guitar, sleep music, café music, study music
```

### 3. Upload via script

```bash
python3 {baseDir}/scripts/upload.py \
  --video "<video-file>" \
  --title "<title>" \
  --description "<description>" \
  --tags "<tags>" \
  --category 10 \
  --privacy private \
  --thumbnail "<thumbnail-file>"
```

See [references/api.md](references/api.md) for YouTube API details and quota limits.

### 4. Post-upload actions

After successful upload:
- Report the video URL: `https://youtu.be/<video-id>`
- Add to playlist if specified
- Set thumbnail if provided (requires verified account for custom thumbnails)
- Save upload metadata to JSON sidecar

### 5. Upload metadata sidecar

```json
{
  "uploaded_at": "2026-03-16T02:00:00Z",
  "video_id": "dQw4w9WgXcQ",
  "url": "https://youtu.be/dQw4w9WgXcQ",
  "title": "Mellow Bedtime Jazz | Piano & Acoustic Guitar",
  "privacy": "private",
  "playlist": "Cozy Jazz Collection",
  "source_video": "2026-03-16-jazz-rainy-evening.mp4"
}
```

## Integration with Pipeline

This is the final step in the production pipeline:

```
music-generation → cover-art-generation → audio-to-video → youtube-upload
                                                               ↓
                                                    Published on YouTube
```

Reads metadata sidecars from upstream skills to auto-generate title, description, and tags.

## Safety

- **Default privacy: `private`** — never auto-publish as public without explicit user confirmation
- Always confirm before uploading: show title, description, and privacy level
- Quota limit: YouTube API allows ~6 uploads per day by default (can request increase)

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| 401 Unauthorized | Token expired | Delete token file, re-authenticate |
| 403 Forbidden | API not enabled or quota exceeded | Check Google Cloud Console |
| `quotaExceeded` | Daily upload limit hit | Wait 24h or request quota increase |
| `uploadLimitExceeded` | Too many uploads | YouTube limits ~100 videos/day |
| Custom thumbnail rejected | Account not verified | Verify phone number on YouTube |
