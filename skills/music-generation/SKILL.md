---
name: music-generation
description: Generate AI music tracks from text prompts with configurable style, lyrics, and duration. Use when someone wants to create music, generate songs, make beats, produce audio tracks, or any request to create audio from a description. Triggers on phrases like "generate music", "create a song", "make a track", "produce beats", "write me a jazz piece". Supports instrumental and vocal tracks, style presets, custom lyrics, and batch generation.
---

# Music Generation

Generate AI music from text prompts via [suno-api-client](https://github.com/chaozc/suno-api-client).

## Provider

Uses **Suno AI** — best-in-class quality for vocal and instrumental music (V5 model). Authentication is cookie-based with interactive hCaptcha solving for datacenter IPs.

See [references/providers.md](references/providers.md) for provider details.

### Prerequisites

- Node.js 18+
- A Suno account (Pro recommended — 2500 credits/mo)
- Chromium (only needed if your IP triggers hCaptcha)

### Setup

1. Install:
   ```bash
   npm install suno-api-client
   # If captcha solving is needed:
   npx playwright install chromium
   ```

2. Get your Suno cookie:
   - Log in to [suno.com](https://suno.com) in your browser
   - Open DevTools → Application → Cookies → `suno.com`
   - Copy all cookies as a single string (`name=value` pairs separated by `; `)

3. Set environment:
   ```bash
   export SUNO_COOKIE="<your-cookie>"
   ```

### Cookie Refresh

Cookies expire periodically (days to weeks). When API calls fail with auth errors, repeat step 2 and update `SUNO_COOKIE`.

## Workflow

### 1. Gather parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| prompt | yes | — | Lyrics or music description |
| tags | no | — | Style/genre tags (e.g., "jazz, mellow, piano, female vocal") |
| title | no | — | Song title |
| instrumental | no | false | Skip vocals entirely |
| model | no | `chirp-v4-5` | Suno model version |
| output-dir | no | `./output/` | Where to save downloaded files |

### 2. Solve captcha (if needed)

Datacenter/VPS IPs almost always trigger hCaptcha. Home IPs usually don't.

```bash
npx suno-captcha
# Saves screenshot → you identify correct images → write answer to .captcha-cmd
# Token saved to .captcha-token
```

Or programmatically:

```javascript
const { solveCaptchaInteractive } = require('suno-api-client');

const result = await solveCaptchaInteractive({
  cookie: process.env.SUNO_COOKIE,
  onScreenshot: (path) => {
    // Send screenshot to user for solving
  }
});
// Write answer: echo "4 5 6" > .captcha-cmd
```

### 3. Generate

**CLI:**

```bash
npx suno-generate \
  --prompt "Verse 1:\nSoft rain on the window..." \
  --tags "jazz, mellow, female vocal, piano, slow waltz" \
  --title "Rainy Evening" \
  --token-file .captcha-token \
  --output-dir ./output
```

**Programmatic:**

```javascript
const { authenticate, generate, waitForCompletion, downloadClips } = require('suno-api-client');

const { jwt } = await authenticate(process.env.SUNO_COOKIE);

const result = await generate(jwt, {
  prompt: 'Verse 1:\nSoft rain on the window...',
  tags: 'jazz, mellow, female vocal, piano, slow waltz',
  title: 'Rainy Evening',
  captchaToken: token  // from captcha solver, or null if not needed
});

const clips = await waitForCompletion(jwt, result.clips.map(c => c.id));
await downloadClips(clips, './output');
```

**Response structure:**

Each generation produces 2 tracks. Clip objects include:
```json
{
  "id": "abc123",
  "title": "Rainy Evening",
  "audio_url": "https://cdn1.suno.ai/abc123.mp3",
  "image_url": "https://cdn2.suno.ai/image_abc123.jpeg",
  "status": "complete",
  "metadata": { "duration": 180, "tags": "jazz, mellow" }
}
```

### 4. File naming

```
<output-dir>/<YYYY-MM-DD>-<title-slug>-<short-id>.mp3
```

Example: `2026-03-16-rainy-evening-abc12345.mp3`

### 5. Metadata sidecar

Save alongside each batch:

```json
{
  "generated_at": "2026-03-16T01:00:00Z",
  "provider": "suno",
  "prompt": "Soft rain on the window...",
  "tags": "jazz, mellow, female vocal, piano, slow waltz",
  "title": "Rainy Evening",
  "instrumental": false,
  "tracks": [
    {
      "id": "abc123",
      "title": "Rainy Evening",
      "status": "complete",
      "duration": 180,
      "audio_url": "https://cdn1.suno.ai/abc123.mp3"
    }
  ]
}
```

### 6. Batch generation

To generate multiple songs (e.g., 10 tracks for a playlist):

1. Solve captcha once (token may work for multiple requests)
2. Prepare a list of prompts (5 prompts × 2 tracks each = 10 songs)
3. Call `generate()` for each prompt sequentially
4. Wait 30-60 seconds between calls to avoid rate limits
5. Download all audio files after generation completes

### 7. Report

After generation, report: file paths, sizes, durations (via `ffprobe`), and prompts used.

## Other Useful API Methods

| Method | Description |
|--------|-------------|
| `getCredits(jwt)` | Check remaining credits |
| `getFeed(jwt)` | Get recent generated songs |
| `isCaptchaRequired(jwt)` | Check if captcha is needed |

## Style Presets

Override with `--tags "free text"`.

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
| 422 Token validation failed | Captcha required | Run captcha solver first |
| Generation timeout | Suno busy | Retry after 2-3 min |
| Rate limited | Too many requests | Wait 60+ seconds between batch calls |

## Limitations

- Suno generates 2 tracks per call (10 credits each)
- Pro plan: 2500 credits/mo (~250 generations)
- Cookie expires periodically — needs manual refresh
- Datacenter IPs trigger captcha; home IPs usually don't
- Unofficial integration — use responsibly
