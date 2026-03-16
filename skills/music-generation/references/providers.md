# Music Generation Providers

## Current: Suno AI via gcui-art/suno-api

- **Repo**: https://github.com/gcui-art/suno-api
- **How it works**: Self-hosted Node.js server that wraps Suno's internal API. Uses your Suno cookie for auth and 2Captcha for automatic hCaptcha solving.
- **Quality**: Best-in-class for vocal music, especially jazz, pop, and lo-fi genres (Suno V5).
- **Cost**: Suno subscription ($10-30/mo) + 2Captcha (~$2-3/1000 solves)
- **Limitations**: Cookie expires periodically; unofficial integration (TOS risk, low for personal use)
- **Setup**: See main SKILL.md

## Alternative: MusicGPT (musicgpt.com)

- **Docs**: https://docs.musicgpt.com
- **How it works**: Official cloud API. Sign up, get API key, call REST endpoints.
- **Quality**: Untested — needs evaluation against Suno V5
- **Cost**: Free tier available, paid plans by usage
- **Advantages**: Official API, no cookie management, no captcha, no TOS risk
- **When to switch**: If Suno cracks down on unofficial API usage, or if MusicGPT quality matches Suno

## Previous: suno-mcp (Playwright browser automation)

- **Repo**: https://github.com/sandraschi/suno-mcp
- **How it works**: Full Playwright browser automation — opens Suno in a headless browser, clicks through the UI
- **Why replaced**: Heavier than gcui-art/suno-api, harder to maintain, SSO login issues
- **Status**: Deprecated in this skill

## Swap Guide

To switch providers:

1. Update SKILL.md's "Provider" section and workflow steps
2. Update API endpoints and request/response format
3. Keep the same file naming convention and metadata sidecar format
4. Test with a single track before batch generation
