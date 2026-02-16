"""
Reference Track Analyzer
Analyze a YouTube or local audio file and generate an Audial prompt that captures its vibe.

Usage:
    python tools/reference_track.py "https://youtube.com/watch?v=..."
    python tools/reference_track.py "https://youtu.be/..."
    python tools/reference_track.py path/to/local/file.mp3
    python tools/reference_track.py "https://youtube.com/watch?v=..." --keep
"""

import sys
import os
import tempfile
import subprocess
import json
import re

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

import numpy as np
import librosa

# Import mood analysis functions from analyze_mood.py
sys.path.insert(0, os.path.dirname(__file__))
from analyze_mood import analyze, tag_mood, KEY_NAMES

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "tracks.json")


def is_url(s: str) -> bool:
    return s.startswith("http://") or s.startswith("https://") or s.startswith("www.")


def get_ffmpeg_path() -> str | None:
    """Find ffmpeg binary — check PATH first, then imageio-ffmpeg fallback."""
    import shutil
    path = shutil.which("ffmpeg")
    if path:
        return path
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return None


def download_audio(url: str, output_dir: str) -> str:
    """Download audio from YouTube URL using yt-dlp."""
    output_path = os.path.join(output_dir, "reference.%(ext)s")

    # Step 1: Download best audio as-is (no ffmpeg needed for download)
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "-f", "bestaudio",
        "--no-playlist",
        "--output", output_path,
        "--quiet",
        "--no-warnings",
        "--no-post-overwrites",
        url,
    ]

    print(f"  downloading audio...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        error = result.stderr.strip() or "download failed"
        raise RuntimeError(f"yt-dlp error: {error}")

    # Find the downloaded file
    raw_file = None
    for f in os.listdir(output_dir):
        if f.startswith("reference"):
            raw_file = os.path.join(output_dir, f)
            break

    if not raw_file:
        raise RuntimeError("download completed but file not found")

    # Step 2: Convert to WAV using ffmpeg (for librosa compatibility)
    wav_file = os.path.join(output_dir, "reference.wav")
    if not raw_file.endswith(".wav"):
        ffmpeg_path = get_ffmpeg_path()
        if ffmpeg_path:
            print(f"  converting to wav...")
            conv = subprocess.run(
                [ffmpeg_path, "-i", raw_file, "-ac", "1", "-ar", "22050",
                 "-y", "-loglevel", "quiet", wav_file],
                capture_output=True, text=True,
            )
            if conv.returncode == 0:
                os.unlink(raw_file)
                return wav_file
        # If ffmpeg conversion fails, try librosa directly on the raw file
        return raw_file

    return raw_file


def get_video_title(url: str) -> str:
    """Get the video title."""
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--get-title",
        "--no-playlist",
        "--quiet",
        "--no-warnings",
        url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else "Unknown"


def analyze_sections(filepath: str, section_duration: float = 15.0) -> list[dict]:
    """Analyze the track in sections to detect changes over time."""
    y, sr = librosa.load(filepath, sr=22050, mono=True)
    total_duration = librosa.get_duration(y=y, sr=sr)

    sections = []
    offset = 0.0

    while offset < total_duration - 5:  # skip last <5s
        end = min(offset + section_duration, total_duration)
        start_sample = int(offset * sr)
        end_sample = int(end * sr)
        section_y = y[start_sample:end_sample]

        # Write section to temp file for analysis
        import soundfile as sf
        tmp_path = os.path.join(tempfile.gettempdir(), f"audial_section_{int(offset)}.wav")
        sf.write(tmp_path, section_y, sr)
        features = analyze(tmp_path)
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

        features["start"] = round(offset, 1)
        features["end"] = round(end, 1)
        sections.append(features)
        offset += section_duration

    return sections


def generate_audial_prompt(features: dict, tags: list[str], title: str = "") -> str:
    """Generate an Audial prompt that captures the vibe of the analyzed track."""
    parts = []

    # Mood/atmosphere
    mood_words = []
    if "very dark" in tags or "dark" in tags:
        mood_words.append("dark")
    elif "very bright" in tags or "bright" in tags:
        mood_words.append("bright")
    if "melancholy" in tags:
        mood_words.append("melancholy")
    elif "uplifting" in tags:
        mood_words.append("uplifting")
    if "still" in tags:
        mood_words.append("still")
    elif "calm" in tags:
        mood_words.append("calm")
    elif "energetic" in tags or "intense" in tags:
        mood_words.append("intense")

    if mood_words:
        parts.append(", ".join(mood_words))

    # Tempo feel
    tempo = features["tempo"]
    if tempo < 70:
        parts.append("very slow tempo")
    elif tempo < 100:
        parts.append(f"slow tempo around {int(tempo)} bpm")
    elif tempo < 130:
        parts.append(f"moderate tempo around {int(tempo)} bpm")
    elif tempo < 160:
        parts.append(f"fast tempo around {int(tempo)} bpm")
    else:
        parts.append(f"very fast around {int(tempo)} bpm")

    # Key
    key_str = f"{features['key']} {features['mode']}"
    parts.append(f"in {key_str}")

    # Texture
    if "sparse" in tags:
        parts.append("sparse and minimal")
    elif "dense" in tags:
        parts.append("layered and dense")

    # Rhythm
    if "ambient" in tags:
        parts.append("ambient, no clear beat")
    elif "gentle rhythm" in tags:
        parts.append("gentle rhythmic pulse")
    elif "rhythmic" in tags:
        parts.append("strong rhythmic drive")

    # Character
    if "noisy/textural" in tags:
        parts.append("textural, noise elements")
    elif "tonal/pure" in tags:
        parts.append("clean tonal sounds")

    prompt = ", ".join(parts)

    return prompt


def print_report(filepath: str, features: dict, tags: list[str], title: str, prompt: str, sections: list[dict] | None = None):
    """Print the full analysis report."""
    print(f"\n{'='*60}")
    print(f"  REFERENCE TRACK ANALYSIS")
    print(f"{'='*60}")
    if title:
        print(f"  Track:     {title}")
    print(f"  File:      {os.path.basename(filepath)}")
    print(f"  Duration:  {features['duration']}s")
    print(f"  Tempo:     {features['tempo']} BPM")
    print(f"  Key:       {features['key']} {features['mode']} (confidence: {features['key_confidence']})")
    print()

    # Visual bars
    bars = [
        ("Energy", features["energy"]),
        ("Brightness", features["brightness"]),
        ("Density", features["density"]),
        ("Rhythm", features["rhythmic_activity"]),
    ]
    for label, val in bars:
        filled = int(val * 20)
        bar = "#" * filled + "-" * (20 - filled)
        print(f"  {label:<12} [{bar}] {val:.2f}")

    print(f"\n  Mood tags:  {', '.join(tags)}")

    # Section analysis (if track is long enough)
    if sections and len(sections) > 1:
        print(f"\n  Track evolution:")
        for s in sections:
            s_tags = tag_mood(s)
            energy_bar = "#" * int(s["energy"] * 10)
            bright_bar = "#" * int(s["brightness"] * 10)
            print(f"    {s['start']:5.0f}s-{s['end']:5.0f}s  E[{energy_bar:<10}] B[{bright_bar:<10}] {s['key']} {s['mode']}")

    print(f"\n  {'='*58}")
    print(f"  AUDIAL PROMPT (paste this into Audial):")
    print(f"  {'='*58}")
    print(f"\n  {prompt}")
    print(f"\n{'='*60}\n")


def extract_youtube_id(url: str) -> str | None:
    """Extract video ID from a YouTube URL."""
    patterns = [
        r'(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'(?:embed/)([a-zA-Z0-9_-]{11})',
    ]
    for pat in patterns:
        m = re.search(pat, url)
        if m:
            return m.group(1)
    return None


def save_to_db(youtube_id: str | None, title: str, features: dict, tags: list[str],
               prompt: str, source_url: str = ""):
    """Save analysis results to the track database."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    # Load existing database
    if os.path.exists(DB_PATH):
        with open(DB_PATH, "r", encoding="utf-8") as f:
            db = json.load(f)
    else:
        db = {"tracks": []}

    # Build track entry
    entry = {
        "title": title,
        "youtube_id": youtube_id or "",
        "game": "",
        "category": "",
        "aliases": [],
        "key": features.get("key", ""),
        "mode": features.get("mode", ""),
        "key_confidence": features.get("key_confidence"),
        "bpm": features.get("tempo"),
        "bpm_feel": None,
        "energy": features.get("energy"),
        "brightness": features.get("brightness"),
        "density": features.get("density"),
        "rhythm": features.get("rhythmic_activity"),
        "duration": features.get("duration"),
        "tags": tags,
        "audial_prompt": prompt,
        "notes": "",
    }

    # Check if track already exists (by youtube_id)
    if youtube_id:
        for i, t in enumerate(db["tracks"]):
            if t.get("youtube_id") == youtube_id:
                # Update existing entry (preserve game/category/aliases/notes)
                entry["game"] = t.get("game", "")
                entry["category"] = t.get("category", "")
                entry["aliases"] = t.get("aliases", [])
                entry["notes"] = t.get("notes", "")
                entry["bpm_feel"] = t.get("bpm_feel")
                db["tracks"][i] = entry
                break
        else:
            db["tracks"].append(entry)
    else:
        db["tracks"].append(entry)

    # Save
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)


def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/reference_track.py <youtube_url_or_file> [--keep] [--no-save]")
        print()
        print("  Analyzes a reference track and generates an Audial prompt.")
        print("  --keep     Keep the downloaded audio file")
        print("  --no-save  Don't save to the track database")
        print()
        print("Examples:")
        print('  python tools/reference_track.py "https://youtube.com/watch?v=dQw4w9WgXcQ"')
        print("  python tools/reference_track.py my_song.mp3")
        sys.exit(1)

    source = sys.argv[1]
    keep_file = "--keep" in sys.argv
    no_save = "--no-save" in sys.argv

    youtube_id = None
    if is_url(source):
        # Download from YouTube
        youtube_id = extract_youtube_id(source)
        title = get_video_title(source)
        print(f"  track: {title}")

        if keep_file:
            dl_dir = os.path.join(os.path.dirname(__file__), "..", "references")
            os.makedirs(dl_dir, exist_ok=True)
            filepath = download_audio(source, dl_dir)
        else:
            tmp_dir = tempfile.mkdtemp()
            filepath = download_audio(source, tmp_dir)
    else:
        # Local file
        filepath = source
        title = os.path.splitext(os.path.basename(source))[0]
        if not os.path.exists(filepath):
            print(f"Error: file not found: {filepath}")
            sys.exit(1)

    try:
        print("  analyzing...")
        features = analyze(filepath)
        tags = tag_mood(features)

        # Section analysis for tracks > 30s
        sections = None
        if features["duration"] > 30:
            sections = analyze_sections(filepath)

        prompt = generate_audial_prompt(features, tags, title)

        print_report(filepath, features, tags, title, prompt, sections)

        # Auto-save to database
        if not no_save:
            save_to_db(youtube_id, title, features, tags, prompt, source)

        if keep_file and is_url(source):
            print(f"  Audio saved: {filepath}")
    finally:
        # Clean up temp files (only if not --keep)
        if is_url(source) and not keep_file:
            try:
                os.unlink(filepath)
                os.rmdir(os.path.dirname(filepath))
            except OSError:
                pass


if __name__ == "__main__":
    main()
