# 🎵 Music Video Production Pipeline

An end-to-end pipeline for generating AI music videos — from song creation to YouTube upload.

## Pipeline Overview

```
music-generation → cover-art-generation → audio-to-video → youtube-upload
```

| Step | What it does |
|------|-------------|
| **music-generation** | Generate AI music tracks from text prompts (style, lyrics, mood) |
| **cover-art-generation** | Create matching cover art from mood/genre descriptions with text overlay |
| **audio-to-video** | Combine audio + cover art into video (single or playlist mode) via ffmpeg |
| **youtube-upload** | Upload to YouTube with auto-generated metadata, tags, and thumbnails |

## Getting Started

### Prerequisites

- Python 3.10+
- ffmpeg (`brew install ffmpeg` / `sudo apt install ffmpeg`)
- Playwright + Chromium (for Suno music generation)
- Google API OAuth2 credentials (for YouTube upload)

### Project Structure

```
music-video-production/
└── skills/
    ├── music-generation/       # AI music creation (Suno backend)
    ├── cover-art-generation/   # AI artwork + text overlay (Pillow)
    ├── audio-to-video/         # ffmpeg audio+image → video
    └── youtube-upload/         # YouTube Data API v3 upload
```

Each skill has its own `SKILL.md` with detailed usage instructions, parameters, and provider configuration.

### Skill Format

Skills follow the [AgentSkill](https://github.com/openclaw/openclaw) format — they're provider-agnostic instruction sets that any AI agent can follow. Each `SKILL.md` defines:

- Input parameters and defaults
- Step-by-step workflow
- Provider swap guide (in `references/`)

## Usage

These skills are designed to be executed by an AI agent (e.g., via OpenClaw). Point your agent at a skill directory and describe what you want:

> "Generate 5 cozy jazz tracks, create cover art for each, combine them into a playlist video, and upload to YouTube"

The agent reads each `SKILL.md` and executes the pipeline step by step.

### Manual / Hybrid Workflow

Some steps may require manual intervention:

- **Suno AI** — no official API; login requires Google SSO. Generate tracks manually on [suno.com](https://suno.com), then feed the audio files into the rest of the pipeline.
- **YouTube OAuth** — first upload requires browser-based consent flow.

## Design Decisions

- **Skills are generic** — no hardcoded paths or platform-specific config
- **Provider-swappable** — each skill documents how to swap backends (e.g., replace Suno with Udio, DALL-E with Midjourney)
- **Text overlay via Pillow** — AI generates clean background images; text (title, artist) is added programmatically with configurable fonts
- **Preferred font**: Playfair Display (classic jazz aesthetic)

## License

MIT
