# Text Overlay with Pillow

Add text (titles, subtitles) to cover art images using Pillow. This gives precise control over font, size, position, and color — far more reliable than asking the image AI to render text.

## Process

1. Generate a clean background image (no text) via the image AI
2. Use Pillow (`PIL.ImageDraw`) to render text on top
3. Choose font based on the music genre/mood (see table below)

## Font Selection by Genre

| Genre/Mood | Recommended Font Style | Example Fonts (Google Fonts) |
|------------|----------------------|------------------------------|
| Jazz, French, elegant | High-contrast serif | Playfair Display, Cormorant |
| Classical, orchestral | Traditional serif | Lora, EB Garamond |
| Lo-fi, chill, modern | Light sans-serif | Josefin Sans, Raleway |
| Electronic, synthwave | Geometric sans | Orbitron, Space Grotesk |
| Folk, acoustic, warm | Rounded serif | Merriweather, Source Serif |
| Hip-hop, bold, urban | Heavy sans-serif | Bebas Neue, Oswald |

Download fonts from [Google Fonts GitHub](https://github.com/google/fonts/tree/main/ofl) as `.ttf` files.

## Pillow Template

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
title_y = int(h * 0.78)

sub_bbox = draw.textbbox((0, 0), subtitle, font=sub_font)
sub_w = sub_bbox[2] - sub_bbox[0]
sub_x = (w - sub_w) // 2
sub_y = title_y + int(h * 0.10)

# Subtle shadow for readability
draw.text((title_x+2, title_y+2), title, font=title_font, fill=(0, 0, 0, 90))
draw.text((title_x, title_y), title, font=title_font, fill=(255, 255, 255, 245))

draw.text((sub_x+2, sub_y+2), subtitle, font=sub_font, fill=(0, 0, 0, 90))
draw.text((sub_x, sub_y), subtitle, font=sub_font, fill=(255, 255, 255, 245))

img.save("cover-final.png", quality=95)
```

## Text Styling Guidelines

- Use Light/Regular weight — avoid bold for elegant genres
- White text with subtle dark shadow for readability on any background
- Title at ~10% of image height, subtitle at ~5%
- Center both lines horizontally and vertically as a group
- Keep text away from edges (minimum 10% margin)
- For RGBA images, use `Image.alpha_composite` for proper transparency blending
