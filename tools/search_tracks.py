"""
Reference Track Search Tool
Search and filter the analyzed track library by any criteria.

Usage:
    python tools/search_tracks.py                          # list all tracks
    python tools/search_tracks.py "final fantasy"          # search by name/game/title
    python tools/search_tracks.py --mood dark              # filter by mood tag
    python tools/search_tracks.py --key "minor"            # all minor keys
    python tools/search_tracks.py --key "D minor"          # specific key
    python tools/search_tracks.py --bpm 80:120             # tempo range
    python tools/search_tracks.py --energy 0.8:1.0         # high energy tracks
    python tools/search_tracks.py --brightness 0:0.1       # very dark tracks
    python tools/search_tracks.py --density 0.8:1.0        # dense/layered
    python tools/search_tracks.py --category "Sacred"      # by category
    python tools/search_tracks.py --game "FFX"             # by game/source
    python tools/search_tracks.py --similar "Julia"        # find similar tracks
    python tools/search_tracks.py --sort energy            # sort by metric
    python tools/search_tracks.py --json                   # output as JSON

Combine filters:
    python tools/search_tracks.py --mood dark --energy 0.8:1.0 --key minor
"""

import sys
import os
import json
import math

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "tracks.json")


def load_db() -> list[dict]:
    if not os.path.exists(DB_PATH):
        print(f"  No track database found at {DB_PATH}")
        print(f"  Run reference_track.py to analyze tracks first.")
        sys.exit(1)
    with open(DB_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("tracks", [])


def parse_range(s: str) -> tuple[float, float]:
    """Parse a range string like '0.5:1.0' or '80:120'."""
    if ":" in s:
        parts = s.split(":")
        lo = float(parts[0]) if parts[0] else -math.inf
        hi = float(parts[1]) if parts[1] else math.inf
        return lo, hi
    # Single value — exact match for BPM, threshold for metrics
    v = float(s)
    return v, v


def matches_text(track: dict, query: str) -> bool:
    """Check if any text field matches the query (case-insensitive)."""
    q = query.lower()
    searchable = [
        track.get("title") or "",
        track.get("game") or "",
        track.get("category") or "",
        track.get("youtube_id") or "",
        track.get("audial_prompt") or "",
        track.get("notes") or "",
    ]
    for alias in (track.get("aliases") or []):
        searchable.append(alias or "")
    for tag in (track.get("tags") or []):
        searchable.append(tag or "")
    return any(q in s.lower() for s in searchable)


def matches_mood(track: dict, mood: str) -> bool:
    m = mood.lower()
    tags = [t.lower() for t in (track.get("tags") or [])]
    prompt = (track.get("audial_prompt") or "").lower()
    title = (track.get("title") or "").lower()
    return any(m in t for t in tags) or m in prompt or m in title


def matches_key(track: dict, key_query: str) -> bool:
    k = key_query.lower()
    track_key = (track.get("key") or "").lower()
    track_mode = (track.get("mode") or "").lower()
    full_key = f"{track_key} {track_mode}".strip()
    return k in full_key


def in_range(value, lo, hi) -> bool:
    if value is None:
        return False
    return lo <= value <= hi


def similarity_score(a: dict, b: dict) -> float:
    """Compute similarity between two tracks based on audio features."""
    score = 0.0
    weights = {"energy": 2.0, "brightness": 2.0, "density": 1.5, "bpm_feel": 1.0}
    for feat, w in weights.items():
        va = a.get(feat) or a.get("bpm")
        vb = b.get(feat) or b.get("bpm")
        if va is not None and vb is not None:
            if feat == "bpm_feel":
                # Normalize BPM to 0-1 scale (40-200 range)
                va = (va - 40) / 160
                vb = (vb - 40) / 160
            diff = abs(va - vb)
            score += w * (1 - diff)
    # Key similarity bonus
    if a.get("mode") == b.get("mode"):
        score += 1.0
    return score


def format_bar(val: float, width: int = 10) -> str:
    if val is None:
        return " " * width
    filled = int(val * width)
    return "#" * filled + "-" * (width - filled)


def print_track(t: dict, verbose: bool = False):
    """Print a single track in compact format."""
    title = t.get("title", "Unknown")
    game = t.get("game", "")
    key = f"{t.get('key', '?')} {t.get('mode', '')}".strip()
    bpm = t.get("bpm_feel") or t.get("bpm", "?")
    energy = t.get("energy")
    brightness = t.get("brightness")
    density = t.get("density")

    game_str = f" ({game})" if game else ""
    print(f"  {title}{game_str}")
    print(f"    Key: {key} | BPM: {bpm} | E:{format_bar(energy)} B:{format_bar(brightness)} D:{format_bar(density)}")

    if verbose:
        yt = t.get("youtube_id", "")
        if yt:
            print(f"    YouTube: watch?v={yt}")
        prompt = t.get("audial_prompt", "")
        if prompt:
            print(f"    Prompt: {prompt}")
        notes = t.get("notes", "")
        if notes:
            print(f"    Notes: {notes}")
    print()


def main():
    args = sys.argv[1:]

    # Parse arguments
    text_query = None
    mood_filter = None
    key_filter = None
    bpm_range = None
    energy_range = None
    brightness_range = None
    density_range = None
    category_filter = None
    game_filter = None
    similar_to = None
    sort_by = None
    output_json = False
    verbose = True
    limit = None

    i = 0
    positionals = []
    while i < len(args):
        arg = args[i]
        if arg == "--mood" and i + 1 < len(args):
            mood_filter = args[i + 1]; i += 2
        elif arg == "--key" and i + 1 < len(args):
            key_filter = args[i + 1]; i += 2
        elif arg == "--bpm" and i + 1 < len(args):
            bpm_range = parse_range(args[i + 1]); i += 2
        elif arg == "--energy" and i + 1 < len(args):
            energy_range = parse_range(args[i + 1]); i += 2
        elif arg == "--brightness" and i + 1 < len(args):
            brightness_range = parse_range(args[i + 1]); i += 2
        elif arg == "--density" and i + 1 < len(args):
            density_range = parse_range(args[i + 1]); i += 2
        elif arg == "--category" and i + 1 < len(args):
            category_filter = args[i + 1]; i += 2
        elif arg == "--game" and i + 1 < len(args):
            game_filter = args[i + 1]; i += 2
        elif arg == "--similar" and i + 1 < len(args):
            similar_to = args[i + 1]; i += 2
        elif arg == "--sort" and i + 1 < len(args):
            sort_by = args[i + 1]; i += 2
        elif arg == "--json":
            output_json = True; i += 1
        elif arg == "--compact":
            verbose = False; i += 1
        elif arg == "--limit" and i + 1 < len(args):
            limit = int(args[i + 1]); i += 2
        elif arg == "--help" or arg == "-h":
            print(__doc__)
            sys.exit(0)
        elif not arg.startswith("--"):
            positionals.append(arg); i += 1
        else:
            print(f"  Unknown option: {arg}")
            sys.exit(1)

    if positionals:
        text_query = " ".join(positionals)

    tracks = load_db()

    # Handle --similar mode
    if similar_to:
        # Find the reference track
        ref = None
        for t in tracks:
            if similar_to.lower() in t.get("title", "").lower():
                ref = t
                break
        if not ref:
            print(f"  Track not found: {similar_to}")
            sys.exit(1)

        # Score all other tracks
        scored = []
        for t in tracks:
            if t.get("youtube_id") == ref.get("youtube_id"):
                continue
            score = similarity_score(ref, t)
            scored.append((score, t))
        scored.sort(key=lambda x: x[0], reverse=True)

        print(f"\n  Tracks similar to: {ref['title']}")
        print(f"  {'='*50}\n")
        for score, t in scored[:limit or 10]:
            print_track(t, verbose=verbose)
        return

    # Apply filters
    results = tracks
    if text_query:
        results = [t for t in results if matches_text(t, text_query)]
    if mood_filter:
        results = [t for t in results if matches_mood(t, mood_filter)]
    if key_filter:
        results = [t for t in results if matches_key(t, key_filter)]
    if bpm_range:
        lo, hi = bpm_range
        results = [t for t in results if in_range(t.get("bpm_feel") or t.get("bpm"), lo, hi)]
    if energy_range:
        lo, hi = energy_range
        results = [t for t in results if in_range(t.get("energy"), lo, hi)]
    if brightness_range:
        lo, hi = brightness_range
        results = [t for t in results if in_range(t.get("brightness"), lo, hi)]
    if density_range:
        lo, hi = density_range
        results = [t for t in results if in_range(t.get("density"), lo, hi)]
    if category_filter:
        cf = category_filter.lower()
        results = [t for t in results if cf in t.get("category", "").lower()]
    if game_filter:
        gf = game_filter.lower()
        results = [t for t in results if gf in t.get("game", "").lower()]

    # Sort
    if sort_by:
        key_map = {
            "energy": lambda t: t.get("energy") or 0,
            "brightness": lambda t: t.get("brightness") or 0,
            "density": lambda t: t.get("density") or 0,
            "bpm": lambda t: t.get("bpm_feel") or t.get("bpm") or 0,
            "title": lambda t: t.get("title", "").lower(),
            "game": lambda t: t.get("game", "").lower(),
            "key": lambda t: t.get("key", ""),
        }
        sort_fn = key_map.get(sort_by)
        if sort_fn:
            reverse = sort_by not in ("title", "game", "key")
            results.sort(key=sort_fn, reverse=reverse)

    if limit:
        results = results[:limit]

    # Output
    if output_json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return

    # Print header
    filters_used = []
    if text_query:
        filters_used.append(f'"{text_query}"')
    if mood_filter:
        filters_used.append(f"mood={mood_filter}")
    if key_filter:
        filters_used.append(f"key={key_filter}")
    if bpm_range:
        filters_used.append(f"bpm={bpm_range[0]}:{bpm_range[1]}")
    if energy_range:
        filters_used.append(f"energy={energy_range[0]}:{energy_range[1]}")
    if category_filter:
        filters_used.append(f"category={category_filter}")
    if game_filter:
        filters_used.append(f"game={game_filter}")

    filter_str = ", ".join(filters_used) if filters_used else "all tracks"
    print(f"\n  Search: {filter_str}")
    print(f"  Found: {len(results)} tracks")
    print(f"  {'='*50}\n")

    for t in results:
        print_track(t, verbose=verbose)


if __name__ == "__main__":
    main()
