# Cover Art Providers

Any image generation tool that accepts a text prompt and outputs an image file.

## Gemini (Nano Banana Pro)

- **Method:** Python script via Gemini API
- **Auth:** `GEMINI_API_KEY` environment variable
- **Strengths:** Good photorealistic quality, supports reference images, aspect ratio control
- **Resolutions:** 1K, 2K, 4K
- **Aspect ratios:** 1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9

```bash
uv run generate_image.py --prompt "..." --filename "output.png" --aspect-ratio 16:9 --resolution 1K
```

## DALL-E (OpenAI)

- **Method:** REST API
- **Auth:** `OPENAI_API_KEY` environment variable
- **Strengths:** High quality, good at artistic styles
- **Sizes:** 1024x1024, 1792x1024, 1024x1792

```bash
curl -X POST https://api.openai.com/v1/images/generations \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "dall-e-3", "prompt": "...", "size": "1792x1024", "quality": "hd"}'
```

## Stable Diffusion (Local or API)

- **Method:** Local inference or API (e.g., Stability AI)
- **Auth:** `STABILITY_API_KEY` for API; none for local
- **Strengths:** Free if local, full control, no content filter
- **Requirements:** GPU for local inference

## Midjourney

- **Method:** Discord bot automation or third-party API wrappers
- **Auth:** Midjourney subscription
- **Strengths:** Excellent artistic quality
- **Limitations:** No official API, automation is fragile

## Provider Selection Guide

| Priority | Provider | Best For |
|----------|----------|----------|
| 1 | Gemini | Default — good quality, easy API, flexible |
| 2 | DALL-E | When higher artistic quality needed |
| 3 | Stable Diffusion | When running locally, no API costs |
| 4 | Midjourney | When maximum artistic quality needed (manual) |
