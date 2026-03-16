---
name: music-generation
description: Generate AI music tracks from text prompts with configurable style, lyrics, and duration. Use when someone wants to create music, generate songs, make beats, produce audio tracks, or any request to create audio from a description. Triggers on phrases like "generate music", "create a song", "make a track", "produce beats", "write me a jazz piece". Supports instrumental and vocal tracks, style presets, custom lyrics, and batch generation. Provider-agnostic — currently uses Suno AI via gcui-art/suno-api.
---

# Music Generation

Generate AI music from text prompts. Provider-swappable: same interface regardless of backend.

## Provider

Currently uses [gcui-art/suno-api](https://github.com/gcui-art/suno-api) — a self-hosted REST API wrapper around Suno AI. It handles authentication, captcha solving, and exposes clean endpoints.

See [references/providers.md](references/providers.md) for provider details and swap guide.

### Prerequisites

- Node.js 18+
- Chromium (for captcha solving via Playwright)
- A [2Captcha](https://2captcha.com) account and API key
- A Suno account (Pro or Premier recommended)

### Setup

1. Clone the repo:
   ```bash
   git clone https://github.com/gcui-art/suno-api.git
   cd suno-api && npm install
   ```

2. Get your Suno cookie:
   - Log in to [suno.com/create](https://suno.com/create) in your browser
   - Open DevTools (F12) → Network tab → refresh the page
   - Find a request containing `?__clerk_api_version`
   - Copy the full `Cookie` header value

3. Configure `.env`:
   ```
   SUNO_COOKIE=<your-cookie>
   TWOCAPTCHA_KEY=<your-2captcha-api-key>
   BROWSER=chromium
   BROWSER_GHOST_CURSOR=false
   BROWSER_LOCALE=en
   BROWSER_HEADLESS=true
   ```

4. Start the server:
   ```bash
   npm run dev    # development (port 3000)
   # or
   npm run build && npm start   # production
   # or
   docker compose build && docker compose up   # Docker
   ```

5. Test: `curl http://localhost:3000/api/get_limit`

### Cookie Refresh

Cookies expire periodically (days to weeks). When API calls start failing with auth errors, repeat step 2 above and update `SUNO_COOKIE` in `.env`, then restart the server.

## Workflow

### 1. Gather parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| prompt | yes | — | Lyrics or music description |
| tags | no | — | Style/genre tags (e.g., "jazz, mellow, piano, female vocal") |
| title | no | — | Song title |
| instrumental | no | false | Skip vocals entirely |
| model | no | `chirp-v3-5` | Suno model version |
| wait_audio | no | true | Wait for generation to complete before returning |
| negative_tags | no | — | Styles to avoid |
| count | no | 2 | Tracks per prompt (Suno generates 2 per call) |
| output-dir | no | `./output/` | Where to save downloaded files |

### 2. Generate

Call the suno-api REST endpoint:

```bash
# Custom generate (with lyrics, style, title)
curl -X POST http://localhost:3000/api/custom_generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Verse 1:\nSoft rain on the window...",
    "tags": "jazz, mellow, female vocal, piano, slow waltz",
    "title": "Rainy Evening",
    "make_instrumental": false,
    "wait_audio": true
  }'

# Simple generate (description only, Suno writes lyrics)
curl -X POST http://localhost:3000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A peaceful evening jazz piece with soft piano",
    "make_instrumental": true,
    "wait_audio": true
  }'
```

Response is a JSON array of audio objects:
```json
[
  {
    "id": "abc123",
    "title": "Rainy Evening",
    "audio_url": "https://cdn1.suno.ai/abc123.mp3",
    "image_url": "https://cdn2.suno.ai/image_abc123.jpeg",
    "lyric": "Soft rain on the window...",
    "duration": "180",
    "status": "complete",
    "tags": "jazz, mellow, female vocal",
    "created_at": "2026-03-16T01:00:00Z"
  }
]
```

### 3. Download audio files

Download each track's `audio_url` to the output directory:

```bash
curl -o output/rainy-evening-01.mp3 "https://cdn1.suno.ai/abc123.mp3"
```

### 4. File naming

```
<output-dir>/<YYYY-MM-DD>-<style>-<short-description>-<NN>.mp3
```

Example: `2026-03-16-jazz-peaceful-evening-01.mp3`

### 5. Metadata sidecar

Save a JSON file alongside each batch:

```json
{
  "generated_at": "2026-03-16T01:00:00Z",
  "provider": "suno",
  "provider_api": "gcui-art/suno-api",
  "prompt": "Soft rain on the window...",
  "tags": "jazz, mellow, female vocal, piano, slow waltz",
  "instrumental": false,
  "tracks": [
    {
      "filename": "2026-03-16-jazz-rainy-evening-01.mp3",
      "duration_seconds": 180,
      "track_id": "abc123",
      "audio_url": "https://cdn1.suno.ai/abc123.mp3",
      "title": "Rainy Evening"
    }
  ]
}
```

### 6. Batch generation

To generate multiple songs (e.g., 10 tracks for a playlist):

1. Prepare a list of prompts (5 prompts × 2 tracks each = 10 songs)
2. Call `/api/custom_generate` for each prompt sequentially (respect rate limits)
3. Wait 30-60 seconds between calls to avoid triggering captchas
4. Download all audio files after generation completes

### 7. Report

After generation, report: file paths, sizes, durations (via `ffprobe`), and the prompts used.

## Other Useful Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/get_limit` | GET | Check remaining credits |
| `/api/get?ids=id1,id2` | GET | Get track info by ID |
| `/api/generate_lyrics` | POST | Generate lyrics from a description |
| `/api/extend_audio` | POST | Extend a track's duration |
| `/api/generate_stems` | POST | Separate vocals and instrumentals |
| `/api/concat` | POST | Concatenate extended tracks into full song |

## Style Presets

Override with `--style-preset <name>` or `--tags "free text"`.

| Preset | Tags |
|--------|------|
| `bedtime-jazz` | mellow, slow soft bedtime jazz, french style, mellow female vocal, piano foundation, acoustic guitar bridge and solo, slow waltz |
| `cozy-cafe` | cozy jazz piano trio, soft brushed drums, warm upright bass, gentle Rhodes piano, intimate café atmosphere |
| `lofi-chill` | lo-fi hip hop, vinyl crackle, mellow piano chords, lazy drums, warm analog bass |
| `ambient-study` | ambient soundscape, soft pads, gentle arpeggios, calm and meditative |
| `bossa-nova` | smooth bossa nova, nylon guitar, soft percussion, warm Brazilian feel |

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| Auth / 401 | Cookie expired | Refresh cookie (see Setup step 2) |
| hCaptcha fail | 2Captcha issue or insufficient balance | Check 2Captcha balance, verify API key |
| Generation timeout | Suno busy | Retry after 2-3 min |
| Rate limited | Too many requests | Wait 60+ seconds between batch calls |

## Limitations

- Free tier: ~5 songs/day. Pro ($10/mo): 500/mo. Premier ($30/mo): 2000/mo.
- Cookie expires periodically — needs manual refresh.
- 2Captcha costs ~$2-3 per 1000 solves (negligible for small batches).
- Suno generates 2 tracks per prompt call.
- This is an unofficial integration — Suno's TOS prohibits scraping.
