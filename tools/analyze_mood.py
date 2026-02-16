"""
Audial Mood Analyzer
Analyzes exported WAV files and outputs mood tags + Audial prompts for adjustment.

Usage:
    python tools/analyze_mood.py path/to/file.wav
    python tools/analyze_mood.py path/to/file.wav --json
"""

import sys
import os

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

import numpy as np
import librosa


# --- Key detection ---

KEY_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Krumhansl-Kessler key profiles
MAJOR_PROFILE = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MINOR_PROFILE = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])


def detect_key(y, sr):
    """Detect musical key using chroma features and Krumhansl-Kessler profiles."""
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    chroma_mean = chroma.mean(axis=1)

    major_corrs = []
    minor_corrs = []
    for i in range(12):
        rolled = np.roll(chroma_mean, -i)
        major_corrs.append(np.corrcoef(rolled, MAJOR_PROFILE)[0, 1])
        minor_corrs.append(np.corrcoef(rolled, MINOR_PROFILE)[0, 1])

    best_major_idx = int(np.argmax(major_corrs))
    best_minor_idx = int(np.argmax(minor_corrs))
    best_major_corr = major_corrs[best_major_idx]
    best_minor_corr = minor_corrs[best_minor_idx]

    if best_major_corr > best_minor_corr:
        return KEY_NAMES[best_major_idx], "major", best_major_corr
    else:
        return KEY_NAMES[best_minor_idx], "minor", best_minor_corr


# --- Feature extraction ---

def analyze(filepath):
    """Extract all mood-relevant features from an audio file."""
    y, sr = librosa.load(filepath, sr=22050, mono=True)
    duration = librosa.get_duration(y=y, sr=sr)

    # Tempo
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    tempo = float(np.atleast_1d(tempo)[0])

    # Key
    key_name, key_mode, key_confidence = detect_key(y, sr)

    # Energy (RMS)
    rms = librosa.feature.rms(y=y)[0]
    energy_mean = float(rms.mean())
    energy_max = float(rms.max())
    # Normalize to 0-1 scale (typical RMS range for music)
    energy_norm = min(1.0, energy_mean / 0.15)

    # Spectral centroid (brightness)
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    brightness = float(centroid.mean())
    # Normalize: <1500 = dark, >4000 = bright
    brightness_norm = min(1.0, max(0.0, (brightness - 500) / 4000))

    # Spectral bandwidth (texture density)
    bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
    density_norm = min(1.0, float(bandwidth.mean()) / 3000)

    # Spectral flatness (noise-like vs tonal)
    flatness = librosa.feature.spectral_flatness(y=y)[0]
    flatness_mean = float(flatness.mean())

    # Zero crossing rate (percussiveness)
    zcr = librosa.feature.zero_crossing_rate(y=y)[0]
    percussiveness = float(zcr.mean())

    # Onset strength (rhythmic activity)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    rhythmic_activity = float(onset_env.mean())
    rhythmic_norm = min(1.0, rhythmic_activity / 15.0)

    # Dynamics (variation in energy)
    dynamics = float(rms.std() / (rms.mean() + 1e-8))

    return {
        "duration": round(duration, 1),
        "tempo": round(tempo, 1),
        "key": key_name,
        "mode": key_mode,
        "key_confidence": round(key_confidence, 2),
        "energy": round(energy_norm, 2),
        "brightness": round(brightness_norm, 2),
        "density": round(density_norm, 2),
        "flatness": round(flatness_mean, 3),
        "percussiveness": round(percussiveness, 3),
        "rhythmic_activity": round(rhythmic_norm, 2),
        "dynamics": round(dynamics, 2),
    }


# --- Mood tagging ---

def tag_mood(features):
    """Convert numeric features into human-readable mood tags."""
    tags = []

    # Energy
    e = features["energy"]
    if e < 0.15:
        tags.append("still")
    elif e < 0.35:
        tags.append("calm")
    elif e < 0.6:
        tags.append("moderate energy")
    elif e < 0.8:
        tags.append("energetic")
    else:
        tags.append("intense")

    # Brightness
    b = features["brightness"]
    if b < 0.2:
        tags.append("very dark")
    elif b < 0.35:
        tags.append("dark")
    elif b < 0.55:
        tags.append("neutral tone")
    elif b < 0.75:
        tags.append("bright")
    else:
        tags.append("very bright")

    # Key/mode
    if features["mode"] == "minor":
        tags.append("melancholy")
    else:
        tags.append("uplifting")

    # Tempo feel
    t = features["tempo"]
    if t < 70:
        tags.append("very slow")
    elif t < 100:
        tags.append("slow")
    elif t < 130:
        tags.append("moderate pace")
    elif t < 160:
        tags.append("fast")
    else:
        tags.append("very fast")

    # Density
    d = features["density"]
    if d < 0.3:
        tags.append("sparse")
    elif d < 0.6:
        tags.append("balanced texture")
    else:
        tags.append("dense")

    # Rhythmic activity
    r = features["rhythmic_activity"]
    if r < 0.2:
        tags.append("ambient")
    elif r < 0.5:
        tags.append("gentle rhythm")
    else:
        tags.append("rhythmic")

    # Texture character
    if features["flatness"] > 0.1:
        tags.append("noisy/textural")
    elif features["flatness"] < 0.01:
        tags.append("tonal/pure")

    return tags


def suggest_changes(features, tags):
    """Based on the analysis, suggest what you could type into Audial to adjust."""
    suggestions = []

    if "very dark" in tags or "dark" in tags:
        suggestions.append(("Brighten", "make it brighter, raise the frequencies, add shimmer"))
    if "very bright" in tags or "bright" in tags:
        suggestions.append(("Darken", "make it darker, lower frequencies, deeper"))
    if "intense" in tags or "energetic" in tags:
        suggestions.append(("Calm down", "softer, less energy, more ambient"))
    if "still" in tags or "calm" in tags:
        suggestions.append(("Add energy", "more movement, add percussion, increase energy"))
    if "very slow" in tags or "slow" in tags:
        suggestions.append(("Speed up", "faster tempo, more momentum"))
    if "fast" in tags or "very fast" in tags:
        suggestions.append(("Slow down", "slower, more spacious, half tempo"))
    if "dense" in tags:
        suggestions.append(("Thin out", "strip it down, fewer layers, minimal"))
    if "sparse" in tags:
        suggestions.append(("Fill out", "add layers, thicker pads, more texture"))
    if "melancholy" in tags:
        suggestions.append(("Uplift", "major key, brighter mood, more hopeful"))
    if "uplifting" in tags:
        suggestions.append(("Darken mood", "minor key, more melancholy, somber"))

    return suggestions


# --- Output ---

def print_report(filepath, features, tags, suggestions):
    """Print a human-readable mood report."""
    print(f"\n{'='*55}")
    print(f"  MOOD ANALYSIS: {os.path.basename(filepath)}")
    print(f"{'='*55}")
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

    if suggestions:
        print(f"\n  To adjust in Audial:")
        for direction, prompt in suggestions:
            print(f"    {direction:<14} -> \"{prompt}\"")

    print(f"{'='*55}\n")


def print_json(features, tags, suggestions):
    """Print machine-readable JSON output."""
    import json
    output = {
        **features,
        "mood_tags": tags,
        "suggestions": [{"direction": d, "prompt": p} for d, p in suggestions],
    }
    print(json.dumps(output, indent=2))


# --- Main ---

def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/analyze_mood.py <audio_file> [--json]")
        print("  Supported: .wav, .mp3, .flac, .ogg")
        sys.exit(1)

    filepath = sys.argv[1]
    use_json = "--json" in sys.argv

    if not os.path.exists(filepath):
        print(f"Error: file not found: {filepath}")
        sys.exit(1)

    features = analyze(filepath)
    tags = tag_mood(features)
    suggestions = suggest_changes(features, tags)

    if use_json:
        print_json(features, tags, suggestions)
    else:
        print_report(filepath, features, tags, suggestions)


if __name__ == "__main__":
    main()
