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

Natural language recommendations:
    python tools/search_tracks.py --recommend "dark sacred slow for Byzantine painting"
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


MOOD_KEYWORDS = {
    # keyword -> (energy_range, brightness_range, mood_tags)
    "dark": ((None, None), (0.0, 0.25), ["dark"]),
    "bright": ((None, None), (0.5, 1.0), ["bright"]),
    "sacred": ((None, None), (None, None), ["sacred", "chant", "religious"]),
    "epic": ((0.7, 1.0), (None, None), ["epic", "intense"]),
    "calm": ((0.0, 0.35), (None, None), ["calm", "still", "ambient"]),
    "melancholy": ((0.1, 0.5), (0.0, 0.3), ["melancholy", "sad"]),
    "intense": ((0.8, 1.0), (None, None), ["intense", "energetic"]),
    "haunting": ((0.1, 0.5), (0.0, 0.2), ["haunting", "eerie"]),
    "triumphant": ((0.7, 1.0), (0.4, 1.0), ["triumphant", "uplifting"]),
    "warm": ((None, None), (0.2, 0.5), ["warm"]),
    "ambient": ((0.0, 0.3), (None, None), ["ambient", "still"]),
    "driving": ((0.7, 1.0), (None, None), ["rhythmic", "energetic"]),
    "gentle": ((0.0, 0.3), (None, None), ["calm", "gentle"]),
    "sparse": ((0.0, 0.3), (None, None), ["sparse"]),
    "dense": ((0.6, 1.0), (None, None), ["dense"]),
    "ancient": ((None, None), (None, None), ["ancient", "medieval", "sacred"]),
    "medieval": ((None, None), (None, None), ["medieval"]),
    "battle": ((0.8, 1.0), (None, None), ["intense", "epic", "battle"]),
    "slow": ((None, None), (None, None), []),
    "fast": ((None, None), (None, None), []),
    "moderate": ((None, None), (None, None), []),
}

TEMPO_HINTS = {
    "very slow": (40, 70),
    "slow": (50, 90),
    "moderate": (80, 120),
    "fast": (120, 170),
    "driving": (110, 160),
}


def parse_description(desc: str) -> dict:
    """Parse a natural language description into search filters."""
    desc_lower = desc.lower()
    filters = {
        "mood_tags": [],
        "energy_lo": None, "energy_hi": None,
        "brightness_lo": None, "brightness_hi": None,
        "bpm_lo": None, "bpm_hi": None,
        "text_queries": [],
    }

    # Extract mood keywords
    for kw, (e_range, b_range, tags) in MOOD_KEYWORDS.items():
        if kw in desc_lower:
            filters["mood_tags"].extend(tags)
            if e_range[0] is not None:
                filters["energy_lo"] = max(filters["energy_lo"] or 0, e_range[0])
            if e_range[1] is not None:
                if filters["energy_hi"] is None:
                    filters["energy_hi"] = e_range[1]
                else:
                    filters["energy_hi"] = min(filters["energy_hi"], e_range[1])
            if b_range[0] is not None:
                filters["brightness_lo"] = max(filters["brightness_lo"] or 0, b_range[0])
            if b_range[1] is not None:
                if filters["brightness_hi"] is None:
                    filters["brightness_hi"] = b_range[1]
                else:
                    filters["brightness_hi"] = min(filters["brightness_hi"], b_range[1])

    # Extract tempo hints
    for hint, (lo, hi) in TEMPO_HINTS.items():
        if hint in desc_lower:
            filters["bpm_lo"] = lo
            filters["bpm_hi"] = hi
            break

    # Remaining words as text queries (skip common filler words)
    filler = {"for", "a", "an", "the", "and", "or", "of", "in", "with", "like", "music",
              "track", "tracks", "song", "songs", "vibe", "vibes", "feel", "feeling",
              "something", "need", "want", "find", "pick", "recommend", "painting",
              "art", "project", "scene", "soundtrack", "background"}
    words = desc_lower.split()
    remaining = [w for w in words if w not in filler and w not in MOOD_KEYWORDS and w not in
                 {w2 for hint in TEMPO_HINTS for w2 in hint.split()}]
    if remaining:
        filters["text_queries"] = remaining

    return filters


def score_track_for_description(track: dict, filters: dict) -> float:
    """Score how well a track matches a parsed description."""
    score = 0.0

    # Mood tag matching
    tags = [t.lower() for t in (track.get("tags") or [])]
    prompt = (track.get("audial_prompt") or "").lower()
    for mood_tag in filters["mood_tags"]:
        mt = mood_tag.lower()
        if any(mt in t for t in tags):
            score += 2.0
        elif mt in prompt:
            score += 1.0

    # Energy range
    energy = track.get("energy")
    if energy is not None:
        elo = filters.get("energy_lo")
        ehi = filters.get("energy_hi")
        if elo is not None and ehi is not None:
            if elo <= energy <= ehi:
                score += 2.0
            else:
                mid = (elo + ehi) / 2
                score -= min(abs(energy - mid), 1.0)
        elif elo is not None and energy >= elo:
            score += 1.0
        elif ehi is not None and energy <= ehi:
            score += 1.0

    # Brightness range
    brightness = track.get("brightness")
    if brightness is not None:
        blo = filters.get("brightness_lo")
        bhi = filters.get("brightness_hi")
        if blo is not None and bhi is not None:
            if blo <= brightness <= bhi:
                score += 2.0
            else:
                mid = (blo + bhi) / 2
                score -= min(abs(brightness - mid), 1.0)
        elif blo is not None and brightness >= blo:
            score += 1.0
        elif bhi is not None and brightness <= bhi:
            score += 1.0

    # BPM range
    bpm = track.get("bpm_feel") or track.get("bpm")
    if bpm is not None:
        bpm_lo = filters.get("bpm_lo")
        bpm_hi = filters.get("bpm_hi")
        if bpm_lo is not None and bpm_hi is not None:
            if bpm_lo <= bpm <= bpm_hi:
                score += 1.5
            else:
                score -= 0.5

    # Text query matching
    for q in filters.get("text_queries", []):
        if matches_text(track, q):
            score += 3.0

    return score


def cmd_recommend(description: str, tracks: list[dict], limit: int = 3):
    """Natural language recommendation mode."""
    filters = parse_description(description)

    scored = []
    for track in tracks:
        s = score_track_for_description(track, filters)
        if s > 0:
            scored.append((s, track))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:limit]

    if not top:
        print(f"\n  No good matches for: \"{description}\"")
        print(f"  Try broader terms or check available moods with: --mood <keyword>")
        return

    print(f"\n  {'='*58}")
    print(f"  TOP {len(top)} RECOMMENDATIONS")
    print(f"  Query: \"{description}\"")
    print(f"  {'='*58}\n")

    for rank, (score, t) in enumerate(top, 1):
        title = t.get("title", "Unknown")
        game = t.get("game", "")
        key = f"{t.get('key', '?')} {t.get('mode', '')}".strip()
        bpm = t.get("bpm_feel") or t.get("bpm", "?")
        energy = t.get("energy")
        brightness = t.get("brightness")
        density = t.get("density")
        yt_id = t.get("youtube_id", "")

        game_str = f" ({game})" if game else ""
        print(f"  #{rank}: {title}{game_str}  [score: {score:.1f}]")
        print(f"    Key: {key} | BPM: {bpm} | E:{format_bar(energy)} B:{format_bar(brightness)} D:{format_bar(density)}")
        if yt_id:
            print(f"    YouTube: watch?v={yt_id}")
        prompt = t.get("audial_prompt", "")
        if prompt:
            print(f"    Audial prompt: {prompt}")
        print()

    # Blended prompt from top 3
    if len(top) >= 2:
        prompts = [t.get("audial_prompt", "") for _, t in top if t.get("audial_prompt")]
        if prompts:
            # Collect unique descriptive fragments (skip key/bpm refs — we add those)
            all_fragments = set()
            for p in prompts:
                for frag in p.split(","):
                    frag = frag.strip()
                    if frag and len(frag) > 3 and not frag.startswith("in ") and "bpm" not in frag:
                        all_fragments.add(frag)
            # Build blended prompt: distinct mood words, avg BPM, best key
            bpms = [t.get("bpm_feel") or t.get("bpm") for _, t in top if (t.get("bpm_feel") or t.get("bpm"))]
            avg_bpm = int(sum(bpms) / len(bpms)) if bpms else None
            keys = [f"{t.get('key','')} {t.get('mode','')}".strip() for _, t in top]

            from collections import Counter
            best_key = Counter(keys).most_common(1)[0][0]

            # Take up to 8 unique fragments, preferring shorter/more descriptive ones
            sorted_frags = sorted(all_fragments, key=len)[:8]
            blended_parts = sorted_frags
            if avg_bpm:
                blended_parts.append(f"around {avg_bpm} bpm")
            if best_key:
                blended_parts.append(f"in {best_key}")

            blended = ", ".join(blended_parts)
            print(f"  {'='*58}")
            print(f"  CUSTOM BLENDED PROMPT")
            print(f"  {'='*58}")
            print(f"\n  {blended}\n")


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
    recommend_desc = None
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
        elif arg == "--recommend" and i + 1 < len(args):
            recommend_desc = args[i + 1]; i += 2
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

    # Handle --recommend mode
    if recommend_desc:
        cmd_recommend(recommend_desc, tracks, limit=limit or 3)
        return

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
