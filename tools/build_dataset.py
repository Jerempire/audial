"""
Build dataset: generate Strudel code for reference tracks via LLM API.

Reads data/tracks.json, selects tracks by category, calls the LLM to generate
Strudel compositions, and saves results to data/song-index.json.

Usage:
  python tools/build_dataset.py --api-key <key>                  # generate all (top N per category)
  python tools/build_dataset.py --api-key <key> --category Sacred --limit 5
  python tools/build_dataset.py --priors-only                    # just rebuild style-priors.json
  python tools/build_dataset.py --dry-run                        # show what would be generated
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TRACKS_PATH = PROJECT_ROOT / "data" / "tracks.json"
SONG_INDEX_PATH = PROJECT_ROOT / "data" / "song-index.json"
STYLE_PRIORS_PATH = PROJECT_ROOT / "data" / "style-priors.json"

# Default limits per category for balanced dataset
DEFAULT_LIMITS = {
    "Sacred/Religious": 6,
    "JRPG": 5,
    "Historical/Roman": 3,
    "Synth/Darkwave": 3,
    "Bollywood/Indian": 3,
    "Strategy Game OST": 3,
    "Medieval/Crusader": 2,
    "Film/Trailer": 2,
    "Celtic": 2,
    "Stealth Game OST": 2,
    "Fighting Game OST": 2,
    "Central Asian/Nomadic": 2,
    "Anime OST": 1,
    "Ambient": 1,
    "Minimalism": 1,
}


def load_tracks() -> list[dict]:
    """Load reference tracks from tracks.json."""
    with open(TRACKS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["tracks"]


def load_existing_index() -> dict:
    """Load existing song-index.json or return empty structure."""
    if SONG_INDEX_PATH.exists():
        with open(SONG_INDEX_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"songs": [], "version": "1.0.0", "generated_at": ""}


def select_tracks(tracks: list[dict], category: str | None, limit: int | None) -> list[dict]:
    """Select tracks for generation, prioritizing energy spread within each category."""
    if category:
        filtered = [t for t in tracks if category.lower() in t.get("category", "").lower()]
        if limit:
            filtered = sorted(filtered, key=lambda t: t.get("energy") or 0.5)
            filtered = spread_select(filtered, limit)
        return filtered

    # Select across all categories using default limits
    selected = []
    by_category: dict[str, list[dict]] = {}
    for t in tracks:
        cat = t.get("category", "Unknown")
        by_category.setdefault(cat, []).append(t)

    for cat, cat_tracks in by_category.items():
        cat_limit = limit or DEFAULT_LIMITS.get(cat, 1)
        sorted_tracks = sorted(cat_tracks, key=lambda t: t.get("energy") or 0.5)
        selected.extend(spread_select(sorted_tracks, cat_limit))

    return selected


def spread_select(sorted_tracks: list[dict], n: int) -> list[dict]:
    """Select n items spread evenly across a sorted list (for energy diversity)."""
    if len(sorted_tracks) <= n:
        return sorted_tracks
    step = len(sorted_tracks) / n
    return [sorted_tracks[int(i * step)] for i in range(n)]


def make_slug(title: str) -> str:
    """Create a slug from a title."""
    return re.sub(r"[^\w]", "", title.lower())


def track_to_id(track: dict) -> str:
    """Generate a stable ID for a track."""
    slug = make_slug(track["title"])
    cat = make_slug(track.get("category", "unknown"))
    return f"{cat}-{slug}"


def build_generation_prompt(track: dict) -> str:
    """Build the prompt to send to the LLM for Strudel code generation."""
    prompt = track.get("audial_prompt", "")
    if not prompt:
        tags = ", ".join(track.get("tags", []))
        key = track.get("key", "C")
        mode = track.get("mode", "major")
        bpm = track.get("bpm", 80)
        prompt = f"{tags}, in {key} {mode}, around {bpm} bpm"

    return prompt


def call_anthropic(prompt: str, api_key: str, model: str = "claude-sonnet-4-5-20250929") -> str | None:
    """Call Anthropic API to generate Strudel code."""
    try:
        import anthropic
    except ImportError:
        print("ERROR: pip install anthropic", file=sys.stderr)
        return None

    client = anthropic.Anthropic(api_key=api_key)

    system_prompt = """You are a Strudel music code generator. Output ONLY valid Strudel code.
Start with setcpm(N). Use 3-6 voices with $: prefix. No prose, no markdown, no explanations.
Use built-in synths: sawtooth, square, sine, triangle, supersaw.
Drums: bd, sd, hh, oh, cp, rim.
Effects: .lpf(), .hpf(), .delay(), .room(), .gain() (max 0.9), .pan().
Keep gains balanced: pads 0.2-0.4, bass 0.3-0.5, drums 0.2-0.4, texture 0.15-0.3."""

    try:
        response = client.messages.create(
            model=model,
            max_tokens=2000,
            system=system_prompt,
            messages=[{"role": "user", "content": f"Create a strudel composition: {prompt}"}],
        )
        text = response.content[0].text.strip()
        # Extract code if wrapped in markdown fences
        if "```" in text:
            match = re.search(r"```(?:javascript|js)?\n?(.*?)```", text, re.DOTALL)
            if match:
                text = match.group(1).strip()
        return text if text.startswith("setcpm(") else None
    except Exception as e:
        print(f"  API error: {e}", file=sys.stderr)
        return None


def call_openai(prompt: str, api_key: str, model: str = "gpt-4o") -> str | None:
    """Call OpenAI API to generate Strudel code."""
    try:
        import openai
    except ImportError:
        print("ERROR: pip install openai", file=sys.stderr)
        return None

    client = openai.OpenAI(api_key=api_key)

    system_prompt = """You are a Strudel music code generator. Output ONLY valid Strudel code.
Start with setcpm(N). Use 3-6 voices with $: prefix. No prose, no markdown, no explanations.
Use built-in synths: sawtooth, square, sine, triangle, supersaw.
Drums: bd, sd, hh, oh, cp, rim.
Effects: .lpf(), .hpf(), .delay(), .room(), .gain() (max 0.9), .pan().
Keep gains balanced: pads 0.2-0.4, bass 0.3-0.5, drums 0.2-0.4, texture 0.15-0.3."""

    try:
        response = client.chat.completions.create(
            model=model,
            max_tokens=2000,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Create a strudel composition: {prompt}"},
            ],
        )
        text = response.choices[0].message.content.strip()
        if "```" in text:
            match = re.search(r"```(?:javascript|js)?\n?(.*?)```", text, re.DOTALL)
            if match:
                text = match.group(1).strip()
        return text if text.startswith("setcpm(") else None
    except Exception as e:
        print(f"  API error: {e}", file=sys.stderr)
        return None


def track_to_song_entry(track: dict, code: str) -> dict:
    """Convert a track + generated code into a SongIndexEntry."""
    tags = track.get("tags", [])
    category = track.get("category", "")

    # Derive genres from category
    genre_map = {
        "JRPG": ["jrpg", "game-ost"],
        "Sacred/Religious": ["sacred", "ambient"],
        "Historical/Roman": ["cinematic", "historical"],
        "Synth/Darkwave": ["synthwave", "darkwave"],
        "Bollywood/Indian": ["bollywood", "world"],
        "Strategy Game OST": ["strategy", "game-ost"],
        "Medieval/Crusader": ["medieval", "cinematic"],
        "Film/Trailer": ["cinematic", "film"],
        "Celtic": ["celtic", "folk"],
        "Stealth Game OST": ["ambient", "game-ost"],
        "Fighting Game OST": ["action", "game-ost"],
        "Central Asian/Nomadic": ["world", "ambient"],
        "Anime OST": ["anime", "game-ost"],
        "Ambient": ["ambient"],
        "Minimalism": ["minimal", "ambient"],
    }
    genres = genre_map.get(category, [category.lower()] if category else ["unknown"])

    # Derive moods from tags
    mood_tags = {"dark", "bright", "tense", "epic", "gentle", "mysterious", "intense",
                 "peaceful", "melancholic", "aggressive", "warm", "ominous", "solemn",
                 "upbeat", "dreamy", "sparse", "lush", "ethereal", "heavy", "playful"}
    moods = [t for t in tags if t.lower() in mood_tags]
    if not moods:
        moods = tags[:3]

    # Derive techniques from code analysis
    techniques = []
    if ".delay(" in code:
        techniques.append("delay")
    if ".room(" in code:
        techniques.append("reverb")
    if ".lpf(" in code:
        techniques.append("filtering")
    if ".slow(" in code and any(f".slow({n})" in code for n in range(4, 9)):
        techniques.append("slow-evolving")
    if "distort" in code or "clip" in code:
        techniques.append("distortion")
    if re.search(r"note\(\"[^\"]*\[.*?,.*?\]", code):
        techniques.append("chords")
    if not techniques:
        techniques = ["basic"]

    # Derive instruments from code
    instruments = []
    for synth in ["sawtooth", "square", "sine", "triangle", "supersaw"]:
        if f'"{synth}"' in code:
            instruments.append(synth)
    for drum in ["bd", "sd", "hh", "oh", "cp", "rim", "sn"]:
        if f'"{drum}' in code or f" {drum}" in code:
            instruments.append(drum)
    if not instruments:
        instruments = ["sawtooth"]

    title = track["title"]
    return {
        "id": track_to_id(track),
        "title": title,
        "author": track.get("game") or track.get("category", "unknown"),
        "source_path": f"generated/{make_slug(title)}",
        "snippet": code,
        "slug": make_slug(title),
        "title_tokens": title.lower().split(),
        "path_tokens": ["generated"] + title.lower().split(),
        "aliases": track.get("aliases", []),
        "genres": genres,
        "moods": moods,
        "techniques": techniques,
        "instruments": instruments,
        "bpm": track.get("bpm_feel") or track.get("bpm"),
        "prompt_seeds": [
            track.get("audial_prompt", ""),
            ", ".join(tags),
        ],
    }


def rebuild_style_priors(songs: list[dict]) -> dict:
    """Analyze the song collection and derive style priors."""
    if not songs:
        return {"summary_bullets": [], "version": "1.0.0", "generated_at": ""}

    bpms = [s["bpm"] for s in songs if s.get("bpm")]
    gains = []
    rooms = []
    lpfs = []

    for s in songs:
        code = s.get("snippet", "")
        for m in re.finditer(r"\.gain\(([\d.]+)\)", code):
            gains.append(float(m.group(1)))
        for m in re.finditer(r"\.room\(([\d.]+)\)", code):
            rooms.append(float(m.group(1)))
        for m in re.finditer(r"\.lpf\((\d+)\)", code):
            lpfs.append(int(m.group(1)))

    all_genres = set()
    all_moods = set()
    all_techniques = set()
    for s in songs:
        all_genres.update(s.get("genres", []))
        all_moods.update(s.get("moods", []))
        all_techniques.update(s.get("techniques", []))

    bullets = []
    if bpms:
        bullets.append(
            f"CPM range: {min(bpms)}-{max(bpms)}, median ~{sorted(bpms)[len(bpms)//2]}. "
            "Slower tempos (40-55) for ambient/sacred, moderate (70-80) for melodic, faster (100+) for percussive/epic"
        )
    bullets.append(
        f"Voice count: 4-5 voices typical. Foundation = drone or pad + bass + melody/texture + percussion"
    )
    if gains:
        bullets.append(
            f"Gain range: {min(gains):.2f}-{max(gains):.2f}. "
            "Pads 0.15-0.25, bass 0.2-0.35, melody 0.08-0.15, drums 0.15-0.4"
        )
    if rooms:
        bullets.append(
            f"Reverb (.room) range: {min(rooms):.1f}-{max(rooms):.1f}. "
            "0.3-0.5 for intimate, 0.7-0.95 for vast/sacred spaces"
        )
    if lpfs:
        bullets.append(
            f"LPF range: {min(lpfs)}-{max(lpfs)}. "
            "Sub-bass 80-120, warm bass 200-500, bright leads 1200+"
        )
    bullets.append(
        "Delay (0.2-0.7) adds depth to sparse melodic lines. Higher delay for ethereal/sacred sounds"
    )
    bullets.append(
        "Common chord voicings: root+fifth+octave for power, root+third+fifth for warmth, extended 7ths for color"
    )
    bullets.append(
        "Slow modifiers (.slow(2-8)) control phrase length. .slow(4) most common for 4-bar phrases"
    )
    bullets.append(
        "Preferred synths: sawtooth (pads, horns), sine (bass, bells), triangle (plucked), square (tension)"
    )
    bullets.append(
        f"Genre coverage: {', '.join(sorted(all_genres)[:10])}"
    )
    bullets.append(
        f"Mood coverage: {', '.join(sorted(all_moods)[:10])}"
    )
    bullets.append(
        "Sub-bass (sine + lpf 80-120) provides physical foundation without muddying the mix"
    )

    from datetime import datetime, timezone
    return {
        "summary_bullets": bullets,
        "version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def save_song_index(data: dict):
    """Save the song index to disk."""
    from datetime import datetime, timezone
    data["generated_at"] = datetime.now(timezone.utc).isoformat()
    with open(SONG_INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(data['songs'])} songs to {SONG_INDEX_PATH}")


def save_style_priors(data: dict):
    """Save style priors to disk."""
    with open(STYLE_PRIORS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(data['summary_bullets'])} style bullets to {STYLE_PRIORS_PATH}")


def main():
    parser = argparse.ArgumentParser(description="Build Audial dataset from reference tracks")
    parser.add_argument("--api-key", help="API key (Anthropic or OpenAI)")
    parser.add_argument("--model", default="claude", choices=["claude", "openai"],
                        help="Which LLM provider to use")
    parser.add_argument("--category", help="Generate only for this category")
    parser.add_argument("--limit", type=int, help="Max tracks per category")
    parser.add_argument("--priors-only", action="store_true", help="Only rebuild style priors from existing songs")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be generated without calling API")
    parser.add_argument("--delay", type=float, default=2.0, help="Seconds between API calls (rate limiting)")
    args = parser.parse_args()

    # Priors-only mode
    if args.priors_only:
        index = load_existing_index()
        priors = rebuild_style_priors(index["songs"])
        save_style_priors(priors)
        return

    if not args.api_key and not args.dry_run:
        # Try environment variable
        args.api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY")
        if not args.api_key:
            print("ERROR: --api-key required or set ANTHROPIC_API_KEY/OPENAI_API_KEY", file=sys.stderr)
            sys.exit(1)

    tracks = load_tracks()
    selected = select_tracks(tracks, args.category, args.limit)
    print(f"Selected {len(selected)} tracks for generation")

    # Load existing index to preserve preset entries
    index = load_existing_index()
    existing_ids = {s["id"] for s in index["songs"]}

    if args.dry_run:
        print("\nDry run — would generate for:")
        for t in selected:
            tid = track_to_id(t)
            status = "SKIP (exists)" if tid in existing_ids else "GENERATE"
            print(f"  [{status}] {t['title']} ({t.get('category', '?')}) — {t.get('audial_prompt', '')[:60]}...")
        return

    # Generate
    call_fn = call_anthropic if args.model == "claude" else call_openai
    generated = 0
    failed = 0

    for i, track in enumerate(selected):
        tid = track_to_id(track)
        if tid in existing_ids:
            print(f"  [{i+1}/{len(selected)}] SKIP {track['title']} (already exists)")
            continue

        prompt = build_generation_prompt(track)
        print(f"  [{i+1}/{len(selected)}] Generating: {track['title']}...")

        code = call_fn(prompt, args.api_key)
        if code:
            entry = track_to_song_entry(track, code)
            index["songs"].append(entry)
            existing_ids.add(tid)
            generated += 1
            print(f"    OK ({len(code)} chars)")
        else:
            failed += 1
            print(f"    FAILED")

        if i < len(selected) - 1:
            time.sleep(args.delay)

    print(f"\nGenerated: {generated}, Failed: {failed}, Total songs: {len(index['songs'])}")

    # Save
    save_song_index(index)

    # Rebuild style priors
    priors = rebuild_style_priors(index["songs"])
    save_style_priors(priors)


if __name__ == "__main__":
    main()
