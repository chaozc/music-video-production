# Music Generation Providers

This skill is provider-agnostic. The interface contract: **text prompt + options → MP3 files + metadata JSON**.

## Current: Suno via suno-mcp

- **Repo:** [sandraschi/suno-mcp](https://github.com/sandraschi/suno-mcp)
- **Method:** Playwright browser automation against suno.com
- **Auth:** Email + password (env vars `SUNO_EMAIL`, `SUNO_PASSWORD`)
- **Pros:** Free tier works, no third-party API needed
- **Cons:** Browser automation is fragile, no official API support

### MCP Tools

| Tool | Purpose |
|------|---------|
| `suno_open_browser` | Launch Playwright browser |
| `suno_login` | Authenticate with Suno |
| `suno_generate_track` | Submit prompt and generate |
| `suno_get_status` | Poll generation status |
| `suno_download_track` | Download completed tracks |
| `suno_close_browser` | Cleanup |

### Pricing (as of 2026)

| Tier | Price | Songs/month | Commercial use |
|------|-------|-------------|----------------|
| Free | $0 | ~5/day | No |
| Pro | $10/mo | 500 | Yes |
| Premier | $30/mo | 2000 | Yes |

## Alternative: Suno via third-party API

Services like APIPASS, Kie.ai, or CometAPI wrap Suno's internal API.

- **Method:** REST API calls
- **Auth:** API key from the third-party service
- **Pros:** Programmatic, no browser needed, faster
- **Cons:** Extra cost, reverse-engineered (may break), legal gray area

To swap: replace the MCP tool calls in the workflow with REST calls to the chosen API. Keep the same file naming and metadata sidecar format.

## Alternative: Suno Official API (future)

As of March 2026, Suno has no official public API. When released:

- Replace browser automation with official REST endpoints
- Switch auth from email/password to API key
- Expect better reliability and rate limits

## Alternative: Udio

- **Site:** udio.com
- **Method:** API or browser automation (TBD)
- **Pros:** Competitive quality, different musical strengths
- **Cons:** Separate account, different parameters

To swap: implement Udio's interface in the generation step, map parameters (prompt, style, lyrics) to Udio equivalents.

## Alternative: Local models (MusicGen, etc.)

- **Method:** Local inference via Hugging Face / PyTorch
- **Pros:** Free, private, no rate limits
- **Cons:** Requires GPU, no vocal/lyrics support, lower quality

To swap: replace MCP calls with local model inference script. Vocal tracks not supported — instrumental only.
