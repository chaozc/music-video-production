---
name: music-generation
description: Generate AI music tracks from text prompts using Suno AI. Use when someone wants to create music, generate songs, make beats, produce audio tracks, or turn lyrics into music. Triggers on "generate music", "create a song", "make a track", "write me a jazz piece", "produce beats", "turn these lyrics into a song". Supports custom lyrics, style tags, instrumental mode, and batch generation. Requires a Suno account cookie from the user.
---

# Music Generation

Generate music via Suno AI using [suno-api-client](https://github.com/chaozc/suno-api-client).

## Setup (one-time)

```bash
npm install github:chaozc/suno-api-client
npx playwright install chromium  # only needed for captcha solving
```

## Workflow

### 1. Get cookie from user

Ask the user for their Suno cookie. Provide these instructions:

> 1. Open [suno.com](https://suno.com) and log in
> 2. Open DevTools (F12) → Application → Cookies → `suno.com`
> 3. Copy all cookies as a single string (name=value pairs separated by `; `)

Store as `SUNO_COOKIE` environment variable.

### 2. Check captcha requirement

```bash
SUNO_COOKIE="$COOKIE" node -e "
  const {authenticate, isCaptchaRequired} = require('suno-api-client');
  (async () => {
    const {jwt} = await authenticate(process.env.SUNO_COOKIE);
    console.log('captcha_required:', await isCaptchaRequired(jwt));
  })();
"
```

- `false` → skip to step 4
- `true` → proceed to step 3

Home IPs rarely trigger captcha. Datacenter/VPS IPs almost always do.

### 3. Solve captcha (interactive)

```bash
SUNO_COOKIE="$COOKIE" npx suno-captcha
```

This launches a headless browser, triggers hCaptcha, and saves a screenshot to `captcha-challenge.png`.

**Agent flow:**
1. Send `captcha-challenge.png` to the user
2. Describe the challenge (question + numbered grid 1-9, left→right top→bottom)
3. User replies with grid numbers (e.g., "4 5 6")
4. Write answer to command file: `echo "4 5 6" > .captcha-cmd`
5. Script clicks cells, submits, saves token to `.captcha-token`

If captcha fails, script saves new screenshot — repeat from step 1.

### 4. Generate

```bash
SUNO_COOKIE="$COOKIE" npx suno-generate \
  --prompt "Verse 1:\nYour lyrics here..." \
  --tags "genre and style tags" \
  --title "Song Title" \
  --token-file .captcha-token \
  --output-dir ./output
```

| Flag | Required | Description |
|------|----------|-------------|
| `--prompt` | yes | Lyrics or description |
| `--tags` | no | Style tags (e.g., "jazz, mellow female vocal, piano, slow waltz") |
| `--title` | no | Song title |
| `--instrumental` | no | Skip vocals |
| `--token-file` | if captcha | Path to saved captcha token |
| `--output-dir` | no | Download directory (default: `./output`) |
| `--no-wait` | no | Don't wait for completion |
| `--no-download` | no | Don't download files |

Each call generates 2 tracks (10 credits each).

### 5. Batch generation

For multiple songs:

1. Solve captcha once (step 3)
2. Call `npx suno-generate` for each prompt sequentially
3. Wait 30-60 seconds between calls to avoid rate limits
4. One captcha token may cover multiple generations

### 6. Output

Files saved to output directory:
- `YYYY-MM-DD-title-slug-shortid.mp3` — audio
- `YYYY-MM-DD-title-slug-shortid-cover.jpeg` — cover image
- `YYYY-MM-DD-title-slug-meta.json` — metadata sidecar

## Style presets

See [references/style-presets.md](references/style-presets.md) for curated tag combinations by genre.

## Troubleshooting

| Error | Fix |
|-------|-----|
| "No active Suno session" | Cookie expired — ask user to refresh |
| "Token validation failed" (422) | Captcha required — run step 3 |
| Generation timeout | Suno busy — retry after 2-3 min |
| Rate limited | Wait 60+ seconds between calls |

## Limitations

- Suno generates 2 tracks per call
- Pro plan: 2500 credits/mo (~250 generations)
- Cookies expire periodically
- Unofficial integration — Suno has no public API
