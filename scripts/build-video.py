#!/usr/bin/env python3
"""Build a YouTube playlist video from cover art + MP3 files."""
import json
import subprocess
import os
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = os.path.expanduser("~/.openclaw/workspace/fonts/PlayfairDisplay.ttf")
COVER_BG = "cover-art.png"
COVER_FINAL = "cover-final.png"
MP3_DIR = "mp3"
OUTPUT_VIDEO = "isaaax-cozy-jazz-playlist.mp4"

# Song order (curated for flow)
SONG_ORDER = [
    "Café-à-Minuit",
    "Letters-Never-Sent",
    "Moonlit-Garden",
    "Sunday-Morning-Rain",
    "Train-to-Nowhere",
    "Starlight-on-the-Seine",
    "Velvet-Hours",
    "Autumn-Bookshop",  # might not exist
    "Lighthouse-Lullaby",
    "Lavender-Fields-at-Dusk",
    "Spring-Came-Quietly",
]

def add_text_overlay():
    """Add title text to cover art."""
    img = Image.open(COVER_BG).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    w, h = img.size
    
    title_font = ImageFont.truetype(FONT_PATH, int(h * 0.08))
    sub_font = ImageFont.truetype(FONT_PATH, int(h * 0.035))
    
    title = "Cozy Jazz Collection"
    subtitle = "Isaaax · Mellow Bedtime Jazz"
    
    # Center title
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_w = title_bbox[2] - title_bbox[0]
    title_x = (w - title_w) // 2
    title_y = int(h * 0.78)
    
    # Center subtitle
    sub_bbox = draw.textbbox((0, 0), subtitle, font=sub_font)
    sub_w = sub_bbox[2] - sub_bbox[0]
    sub_x = (w - sub_w) // 2
    sub_y = title_y + int(h * 0.10)
    
    # Semi-transparent dark band behind text
    band_y1 = title_y - int(h * 0.03)
    band_y2 = sub_y + int(h * 0.06)
    draw.rectangle([(0, band_y1), (w, band_y2)], fill=(0, 0, 0, 100))
    
    # Shadow + text
    for text, font, x, y in [(title, title_font, title_x, title_y), (subtitle, sub_font, sub_x, sub_y)]:
        draw.text((x+2, y+2), text, font=font, fill=(0, 0, 0, 120))
        draw.text((x, y), text, font=font, fill=(255, 255, 255, 240))
    
    result = Image.alpha_composite(img, overlay)
    result.convert("RGB").save(COVER_FINAL, quality=95)
    print(f"✅ Cover with text: {COVER_FINAL}")

def get_mp3_files():
    """Get ordered list of MP3 files."""
    available = os.listdir(MP3_DIR)
    ordered = []
    for name in SONG_ORDER:
        filename = name + ".mp3"
        if filename in available:
            ordered.append(filename)
            available.remove(filename)
    # Add any remaining files not in the order list
    for f in sorted(available):
        if f.endswith(".mp3"):
            ordered.append(f)
    return ordered

def get_duration(filepath):
    """Get audio duration in seconds."""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", filepath],
        capture_output=True, text=True
    )
    return float(result.stdout.strip())

def build_video():
    """Concatenate MP3s and combine with cover art into a video."""
    mp3_files = get_mp3_files()
    print(f"\n🎵 {len(mp3_files)} songs:")
    
    # Build concat file and track timestamps
    timestamps = []
    current_time = 0
    concat_list = "concat-list.txt"
    
    with open(concat_list, "w") as f:
        for mp3 in mp3_files:
            filepath = os.path.join(MP3_DIR, mp3)
            duration = get_duration(filepath)
            title = mp3.replace(".mp3", "").replace("-", " ")
            
            minutes = int(current_time // 60)
            seconds = int(current_time % 60)
            timestamp = f"{minutes:02d}:{seconds:02d}"
            timestamps.append((timestamp, title))
            print(f"  {timestamp} - {title} ({duration:.0f}s)")
            
            f.write(f"file '{filepath}'\n")
            current_time += duration
    
    total_min = int(current_time // 60)
    total_sec = int(current_time % 60)
    print(f"\n📊 Total duration: {total_min}:{total_sec:02d}")
    
    # Concat audio
    print("\n🔗 Concatenating audio...")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
        "-c", "copy", "combined-audio.mp3"
    ], check=True, capture_output=True)
    
    # Create video with cover art + audio
    print("🎬 Creating video...")
    subprocess.run([
        "ffmpeg", "-y",
        "-loop", "1", "-i", COVER_FINAL,
        "-i", "combined-audio.mp3",
        "-c:v", "libx264", "-tune", "stillimage",
        "-c:a", "aac", "-b:a", "192k",
        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:-1:-1:color=black",
        "-pix_fmt", "yuv420p",
        "-shortest",
        OUTPUT_VIDEO
    ], check=True, capture_output=True)
    
    size_mb = os.path.getsize(OUTPUT_VIDEO) / 1024 / 1024
    print(f"✅ Video: {OUTPUT_VIDEO} ({size_mb:.1f}MB)")
    
    # Generate YouTube metadata
    timestamp_text = "\n".join(f"{ts} {title}" for ts, title in timestamps)
    
    metadata = {
        "title": "Cozy Bedtime Jazz | Relaxing Piano & Acoustic Guitar · Isaaax",
        "description": f"""☕ A cozy collection of mellow jazz for your evening wind-down.

Perfect for: sleeping, studying, reading, relaxing, working from home
🎹 Instruments: piano, acoustic guitar, soft female vocals
☕ Mood: warm, cozy, French café vibes

📋 Tracklist:
{timestamp_text}

Subscribe for more cozy jazz playlists 🎵

#jazz #cozyjazz #bedtimejazz #relaxingmusic #pianomusic #studymusic #cafémusic #sleepmusic #frenchjazz #acousticguitar""",
        "tags": "jazz, cozy jazz, bedtime jazz, relaxing piano, acoustic guitar, sleep music, café music, study music, french jazz, mellow jazz, soft vocals, lo-fi jazz, evening jazz, piano jazz",
        "category": 10,
        "privacy": "private",
        "timestamps": timestamps
    }
    
    with open("youtube-metadata.json", "w") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"📝 Metadata: youtube-metadata.json")
    
    # Print metadata for review
    print(f"\n{'='*50}")
    print(f"Title: {metadata['title']}")
    print(f"\nDescription:\n{metadata['description']}")
    
    os.remove(concat_list)

if __name__ == "__main__":
    add_text_overlay()
    build_video()
