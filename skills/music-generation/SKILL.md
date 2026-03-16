---
name: music-generation
description: Generate AI music tracks from text prompts with configurable style, lyrics, and duration. Use when someone wants to create music, generate songs, make beats, produce audio tracks, or any request to create audio from a description. Triggers on phrases like "generate music", "create a song", "make a track", "produce beats", "write me a jazz piece". Supports instrumental and vocal tracks, style presets, custom lyrics, and batch generation. Provider-agnostic — currently uses Suno AI via browser automation, swappable to other backends.
---

# Music Generation

Generate AI music from text prompts. Provider-swappable: same interface regardless of backend.

## Provider

Currently uses [suno-mcp](https://github.com/sandraschi/suno-mcp) (Playwright browser automation for Suno AI). See [references/providers.md](references/providers.md) for provider details and swap guide.

### Credentials

Set as environment variables or in `~/.openclaw/openclaw.json` under `skills.music-generation.env`:
- `SUNO_EMAIL` — Suno account email
- `SUNO_PASSWORD` — Suno account password

### Prerequisites

- Python 3.10+
- Playwright + Chromium: `pip install playwright && playwright install chromium`
- suno-mcp: `pip install -r <suno-mcp-repo>/requirements.txt`

## Workflow

### 1. Gather parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| prompt | yes | — | Music description or mood |
| style-preset | no | `bedtime-jazz` | Named preset (see Style Presets below) |
| style | no | — | Free-text style (overrides preset) |
| lyrics | no | — | Custom lyrics text |
| instrumental | no | false | Skip vocals entirely |
| count | no | 2 | Tracks to generate (Suno generates 2 per prompt) |
| output-dir | no | `~/Music/suno-generated/` | Output directory |

### 2. Generate

Using suno-mcp MCP tools in sequence:

```javascript
suno_open_browser({ headless: true })
suno_login({ email: $SUNO_EMAIL, password: $SUNO_PASSWORD })
suno_generate_track({ prompt: "<resolved style + prompt>", style: "<genre>", lyrics: "<lyrics or empty>" })
suno_get_status()
suno_download_track({ track_id: "<id>", download_path: "<output-dir>" })
suno_close_browser()
```

### 3. File naming

```
<output-dir>/<YYYY-MM-DD>-<style>-<short-description>-<NN>.mp3
```

Example: `2026-03-16-jazz-peaceful-evening-01.mp3`

### 4. Metadata sidecar

Save a JSON file alongside each batch:

```json
{
  "generated_at": "2026-03-16T01:00:00Z",
  "provider": "suno",
  "prompt": "a peaceful evening melody",
  "style_preset": "bedtime-jazz",
  "resolved_style": "Mellow, slow soft bedtime jazz, french style...",
  "instrumental": true,
  "tracks": [
    { "filename": "2026-03-16-jazz-peaceful-evening-01.mp3", "duration_seconds": 180, "track_id": "abc123" }
  ]
}
```

### 5. Report

After generation, report: file paths, sizes, durations (via `ffprobe`), and the prompt used.

## Style Presets

Default: `bedtime-jazz`. Override with `--style-preset <name>` or `--style "free text"`.

| Preset | Description |
|--------|-------------|
| `bedtime-jazz` | Mellow, slow soft bedtime jazz, french style, mellow female vocal, piano foundation, acoustic guitar bridge and solo, slow waltz |
| `cozy-cafe` | Cozy jazz piano trio, soft brushed drums, warm upright bass, gentle Rhodes piano, intimate café atmosphere |
| `lofi-chill` | Lo-fi hip hop, vinyl crackle, mellow piano chords, lazy drums, warm analog bass |
| `ambient-study` | Ambient soundscape, soft pads, gentle arpeggios, calm and meditative |
| `bossa-nova` | Smooth bossa nova, nylon guitar, soft percussion, warm Brazilian feel |

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| Login failed | Bad credentials or 2FA | Check env vars, disable 2FA |
| Generation timeout | Suno busy | Retry after 2-3 min |
| Browser crash | Playwright issue | Try `headless: false` |
| Rate limited | Too many requests | Wait 10+ min between batches |

## Limitations

- Free tier: ~5 songs/day. Pro ($10/mo): 500/mo. Premier ($30/mo): 2000/mo.
- Browser automation may break on Suno UI changes.
- Generation takes 1-3 min per batch.
