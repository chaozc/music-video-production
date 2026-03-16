# Music Generation Providers

## Current: Suno AI via suno-api-client

- **Client**: https://github.com/chaozc/suno-api-client
- **How it works**: Node.js client that authenticates with your Suno cookie, handles hCaptcha interactively, generates music via Suno's internal API, and downloads completed tracks.
- **Quality**: Best-in-class for vocal music — jazz, pop, lo-fi, and most genres (Suno V5 model).
- **Cost**: Suno subscription only ($10/mo Pro = 2500 credits). No third-party captcha service needed — captcha is solved interactively (human-in-the-loop).
- **Limitations**: Cookie expires periodically; datacenter IPs require captcha; unofficial integration.
- **Setup**: See main SKILL.md

## Swap Guide

To switch to a different provider:

1. Update SKILL.md's "Provider" section and workflow steps
2. Update API calls and response parsing
3. Keep the same file naming convention and metadata sidecar format
4. Test with a single track before batch generation
