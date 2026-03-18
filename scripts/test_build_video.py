#!/usr/bin/env python3
"""Tests for build-video.py"""
import json
import os
import subprocess
import sys
import tempfile
import shutil

import pytest

# Import functions from build-video
sys.path.insert(0, os.path.dirname(__file__))
import importlib
build_video = importlib.import_module("build-video")


# ── Fixtures ──

@pytest.fixture(scope="session")
def tmp_base():
    """Session-scoped temp directory, cleaned up at end."""
    d = tempfile.mkdtemp(prefix="bv-test-")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture(scope="session")
def silent_mp3(tmp_base):
    """Generate a 3-second silent MP3."""
    path = os.path.join(tmp_base, "silent.mp3")
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
        "-t", "3", "-c:a", "libmp3lame", "-b:a", "128k", path
    ], check=True, capture_output=True)
    return path


@pytest.fixture(scope="session")
def cover_image(tmp_base):
    """Generate a 200x200 red test image."""
    path = os.path.join(tmp_base, "cover.png")
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=red:s=200x200:d=1",
        "-frames:v", "1", path
    ], check=True, capture_output=True)
    return path


@pytest.fixture(scope="session")
def mp3_dir(tmp_base):
    """Directory with 3 short silent MP3s."""
    d = os.path.join(tmp_base, "songs")
    os.makedirs(d, exist_ok=True)
    for name in ["Alpha-Song.mp3", "Beta-Track.mp3", "Gamma-Tune.mp3"]:
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
            "-t", "2", "-c:a", "libmp3lame", "-b:a", "128k",
            os.path.join(d, name)
        ], check=True, capture_output=True)
    return d


@pytest.fixture
def font_path():
    """Find a usable TTF font for text overlay tests."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for f in candidates:
        if os.path.exists(f):
            return f
    pytest.skip("No TTF font found on system")


# ── Unit Tests: Pure Functions ──

class TestFormatTimestamp:
    def test_zero(self):
        assert build_video.format_timestamp(0) == "00:00"

    def test_seconds_only(self):
        assert build_video.format_timestamp(45) == "00:45"

    def test_minutes_and_seconds(self):
        assert build_video.format_timestamp(125) == "02:05"

    def test_hour(self):
        assert build_video.format_timestamp(3661) == "1:01:01"

    def test_fractional_seconds(self):
        assert build_video.format_timestamp(90.7) == "01:30"


class TestGetAudioFiles:
    def test_sorted_by_default(self, mp3_dir):
        files = build_video.get_audio_files(mp3_dir)
        assert files == ["Alpha-Song.mp3", "Beta-Track.mp3", "Gamma-Tune.mp3"]

    def test_custom_order(self, mp3_dir):
        files = build_video.get_audio_files(mp3_dir, order="Gamma-Tune.mp3,Alpha-Song.mp3")
        assert files[0] == "Gamma-Tune.mp3"
        assert files[1] == "Alpha-Song.mp3"
        # Remaining file appended
        assert "Beta-Track.mp3" in files

    def test_missing_in_order_skipped(self, mp3_dir):
        files = build_video.get_audio_files(mp3_dir, order="Nonexistent.mp3,Alpha-Song.mp3")
        assert files[0] == "Alpha-Song.mp3"
        assert "Nonexistent.mp3" not in files

    def test_ignores_non_audio(self, mp3_dir):
        # Create a non-audio file
        txt = os.path.join(mp3_dir, "readme.txt")
        open(txt, "w").close()
        try:
            files = build_video.get_audio_files(mp3_dir)
            assert "readme.txt" not in files
        finally:
            os.remove(txt)

    def test_empty_dir(self, tmp_base):
        empty = os.path.join(tmp_base, "empty")
        os.makedirs(empty, exist_ok=True)
        assert build_video.get_audio_files(empty) == []


class TestGetDuration:
    def test_duration(self, silent_mp3):
        dur = build_video.get_duration(silent_mp3)
        assert 2.5 < dur < 3.5  # ~3 seconds, allow ffmpeg tolerance


# ── Integration Tests: Video Building ──

class TestBuildSingle:
    def test_creates_video(self, silent_mp3, cover_image, tmp_base):
        output = os.path.join(tmp_base, "test-single.mp4")
        build_video.build_single(silent_mp3, cover_image, output, "1920x1080", "192k")

        assert os.path.exists(output)
        assert os.path.getsize(output) > 0

        # Verify it's a valid video with ~3s duration
        dur = build_video.get_duration(output)
        assert 2.5 < dur < 3.5

    def test_custom_resolution(self, silent_mp3, cover_image, tmp_base):
        output = os.path.join(tmp_base, "test-720p.mp4")
        build_video.build_single(silent_mp3, cover_image, output, "1280x720", "128k")

        assert os.path.exists(output)
        # Check resolution via ffprobe
        result = subprocess.run([
            "ffprobe", "-v", "quiet", "-select_streams", "v:0",
            "-show_entries", "stream=width,height", "-of", "csv=p=0", output
        ], capture_output=True, text=True)
        w, h = result.stdout.strip().split(",")
        assert int(w) == 1280
        assert int(h) == 720


class TestBuildPlaylist:
    def test_creates_concatenated_video(self, mp3_dir, cover_image, tmp_base):
        audio_files = ["Alpha-Song.mp3", "Beta-Track.mp3", "Gamma-Tune.mp3"]
        output = os.path.join(tmp_base, "test-playlist.mp4")

        timestamps = build_video.build_playlist(
            mp3_dir, audio_files, cover_image, output, "1920x1080", "192k"
        )

        assert os.path.exists(output)
        assert os.path.getsize(output) > 0

        # 3 tracks × ~2s each ≈ 6s
        dur = build_video.get_duration(output)
        assert 4.0 < dur < 9.0

        # Timestamps
        assert len(timestamps) == 3
        assert timestamps[0]["timestamp"] == "00:00"
        assert timestamps[0]["title"] == "Alpha Song"

    def test_timestamps_progression(self, mp3_dir, cover_image, tmp_base):
        audio_files = ["Alpha-Song.mp3", "Beta-Track.mp3"]
        output = os.path.join(tmp_base, "test-playlist-ts.mp4")

        timestamps = build_video.build_playlist(
            mp3_dir, audio_files, cover_image, output, "1920x1080", "192k"
        )

        # Second track should start after first
        assert timestamps[1]["seconds"] > 0


class TestTextOverlay:
    def test_creates_overlay_image(self, cover_image, font_path, tmp_base):
        output = os.path.join(tmp_base, "cover-overlay.png")
        build_video.add_text_overlay(cover_image, "Test Title", "Test Sub", font_path, output)

        assert os.path.exists(output)
        assert os.path.getsize(output) > 0

        from PIL import Image
        img = Image.open(output)
        assert img.size[0] > 0
        assert img.size[1] > 0

    def test_overlay_without_subtitle(self, cover_image, font_path, tmp_base):
        output = os.path.join(tmp_base, "cover-no-sub.png")
        build_video.add_text_overlay(cover_image, "Title Only", None, font_path, output)

        assert os.path.exists(output)
