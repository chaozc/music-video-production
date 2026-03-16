---
name: cover-art-generation
description: Generate cover art images for music tracks, albums, or videos based on mood, genre, and style descriptions. Use when someone needs artwork for a song, album cover, YouTube thumbnail, or any visual that accompanies audio content. Triggers on phrases like "generate cover art", "create album art", "make a thumbnail", "design artwork for my track", "generate an image for this song". Supports multiple image AI providers and consistent style presets for channel branding.
---

# Cover Art Generation

Generate cover art images from text descriptions, matched to music mood and genre. Provider-agnostic — works with any image generation API or tool.

## Provider

Use whichever image generation tool is available in your environment:
- **Gemini (Nano Banana Pro)** — good photorealistic and artistic quality
- **DALL-E** — OpenAI's image generation API
- **Midjourney** — via API or automation
- **Stable Diffusion** — local or API-based
- **Any tool that accepts a text prompt and outputs an image file**

See [references/providers.md](references/providers.md) for provider-specific setup.

## Workflow

### 1. Gather parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| mood | yes | — | Music mood/vibe (e.g., "cozy evening", "energetic sunrise") |
| genre | no | `jazz` | Music genre for visual style matching |
| style-preset | no | `warm-cozy` | Named visual preset (see Style Presets below) |
| style | no | — | Free-text visual style (overrides preset) |
| text-overlay | no | — | Text to render on the image (e.g., song title) |
| aspect-ratio | no | `16:9` | Output aspect ratio (`16:9` for YouTube, `1:1` for album, `9:16` for stories) |
| resolution | no | `1K` | Output resolution |
| count | no | 1 | Number of variations to generate |
| output-dir | no | `./covers/` | Output directory |

### 2. Build the prompt

Combine mood, genre, and style into an image generation prompt:

```
<visual style preset> + <mood description> + <genre-appropriate visual elements> + <technical quality tags>
```

Example for bedtime jazz:
```
Warm cozy café interior at night, soft golden lamp light, rain on the window, 
a piano in the corner, coffee cup with steam, vintage film photography style, 
warm color palette, soft focus, cinematic lighting, 4K quality
```

**Key rules:**
- Match visuals to the music mood, not literal lyrics
- Keep a consistent visual identity across tracks for the same channel
- **Always generate the image without any text** — text overlay is added separately via Pillow (see step 3b)
- Include technical quality tags: "4K quality", "professional photography", "cinematic lighting"
- Add "no text, no words, no letters, no watermark" to the prompt to prevent AI-generated text artifacts

### 3. Generate

Call the available image generation tool with the built prompt. Example:

```bash
# Gemini / Nano Banana Pro
generate_image.py --prompt "<built prompt>" --filename "<output-path>" --aspect-ratio 16:9 --resolution 1K

# DALL-E
curl -X POST https://api.openai.com/v1/images/generations \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{"prompt": "<built prompt>", "size": "1792x1024"}'

# Any other tool — adapt accordingly
```

### 3b. Text overlay (Pillow)

When `text-overlay` is provided, use Pillow to overlay text on the generated image. This gives precise control over font, size, position, and color — far more reliable than asking the image AI to render text.

**Process:**
1. Generate a clean background image (no text) via the image AI
2. Use Pillow (`PIL.ImageDraw`) to render text on top
3. Choose font based on the music genre/mood:

**Font selection by genre:**

| Genre/Mood | Recommended Font Style | Example Fonts (Google Fonts) |
|------------|----------------------|------------------------------|
| Jazz, French, elegant | High-contrast serif | Playfair Display, Cormorant |
| Classical, orchestral | Traditional serif | Lora, EB Garamond |
| Lo-fi, chill, modern | Light sans-serif | Josefin Sans, Raleway |
| Electronic, synthwave | Geometric sans | Orbitron, Space Grotesk |
| Folk, acoustic, warm | Rounded serif | Merriweather, Source Serif |
| Hip-hop, bold, urban | Heavy sans-serif | Bebas Neue, Oswald |

Download fonts from [Google Fonts GitHub](https://github.com/google/fonts/tree/main/ofl) as `.ttf` files.

**Pillow text overlay template:**

```python
from PIL import Image, ImageDraw, ImageFont

img = Image.open("background.png")
draw = ImageDraw.Draw(img)
w, h = img.size

title_font = ImageFont.truetype("font.ttf", int(h * 0.10))
sub_font = ImageFont.truetype("font.ttf", int(h * 0.05))

title = "Album Title"
subtitle = "by Artist"

# Center text
title_bbox = draw.textbbox((0, 0), title, font=title_font)
title_w = title_bbox[2] - title_bbox[0]
title_x = (w - title_w) // 2
# ... (center vertically similarly)

# Subtle shadow for readability
draw.text((title_x+2, title_y+2), title, font=title_font, fill=(0, 0, 0, 90))
# Main text
draw.text((title_x, title_y), title, font=title_font, fill=(255, 255, 255, 245))

img.save("cover-final.png", quality=95)
```

**Text styling guidelines:**
- Use Light/Regular weight — avoid bold for elegant genres
- White text with subtle dark shadow for readability on any background
- Title at ~10% of image height, subtitle at ~5%
- Center both lines horizontally and vertically as a group
- Keep text away from edges (minimum 10% margin)

### 4. File naming

```
<output-dir>/<YYYY-MM-DD>-<genre>-<short-description>-cover-<NN>.png
```

Example: `2026-03-16-jazz-rainy-evening-cover-01.png`

### 5. Metadata sidecar

Save alongside the image:

```json
{
  "generated_at": "2026-03-16T01:00:00Z",
  "provider": "gemini",
  "prompt": "Warm cozy café interior at night...",
  "mood": "cozy evening",
  "genre": "jazz",
  "style_preset": "warm-cozy",
  "aspect_ratio": "16:9",
  "filename": "2026-03-16-jazz-rainy-evening-cover-01.png"
}
```

## Style Presets

Default: `warm-cozy`. Override with `--style-preset <name>` or `--style "free text"`.

| Preset | Visual Description |
|--------|-------------------|
| `warm-cozy` | Warm golden tones, soft lighting, café/home interior, rain, candles, vintage film look |
| `night-city` | Night cityscape, neon reflections, wet streets, moody blue-purple palette, cinematic |
| `nature-calm` | Soft natural light, forest/lake/garden, gentle mist, pastel earth tones |
| `vintage-vinyl` | Retro vinyl record aesthetic, grainy texture, 70s color palette, warm analog feel |
| `minimal-abstract` | Clean minimal composition, geometric shapes, muted colors, modern art feel |

## Integration with Pipeline

This skill receives input from `music-generation` (or manual track selection) and outputs to `audio-to-video`:

```
music-generation → metadata JSON (mood, genre, style)
                        ↓
              cover-art-generation → cover image file
                        ↓
                  audio-to-video → final video
```

When a metadata sidecar JSON from music-generation is available, read `style_preset` and `prompt` to automatically derive the mood and genre for cover art.

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| Safety filter blocked | Prompt triggered content filter | Rephrase prompt, remove potentially flagged terms |
| Generation timeout | Provider overloaded | Retry after 1-2 min |
| Low quality output | Prompt too vague | Add more specific visual details and quality tags |
| Wrong aspect ratio | Provider doesn't support requested ratio | Check provider capabilities, crop/pad after generation |
