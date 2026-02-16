"""
Music Project Mood Board Manager
Create and manage project-based track collections for art/creative projects.

Usage:
    python tools/music_project.py list                          # list all projects
    python tools/music_project.py show <project>                # show project details
    python tools/music_project.py create <project>              # create new project
    python tools/music_project.py add <project> <youtube_id>    # add track to project
    python tools/music_project.py remove <project> <youtube_id> # remove track
    python tools/music_project.py suggest <project>             # suggest tracks from DB
"""

import sys
import os
import json

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

import yaml

PROJECTS_DIR = os.path.join(os.path.dirname(__file__), "..", "projects")
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "tracks.json")


def load_db() -> list[dict]:
    if not os.path.exists(DB_PATH):
        return []
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f).get("tracks", [])


def load_project(name: str) -> dict | None:
    path = os.path.join(PROJECTS_DIR, f"{name}.yaml")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_project(name: str, project: dict):
    os.makedirs(PROJECTS_DIR, exist_ok=True)
    path = os.path.join(PROJECTS_DIR, f"{name}.yaml")
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(project, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def find_track(tracks: list[dict], youtube_id: str) -> dict | None:
    for t in tracks:
        if t.get("youtube_id") == youtube_id:
            return t
    return None


def format_bar(val, width=10):
    if val is None:
        return "-" * width
    filled = int(val * width)
    return "#" * filled + "-" * (width - filled)


def cmd_list():
    os.makedirs(PROJECTS_DIR, exist_ok=True)
    files = [f for f in os.listdir(PROJECTS_DIR) if f.endswith(".yaml")]
    if not files:
        print("  No projects yet. Create one with: python tools/music_project.py create <name>")
        return
    print(f"\n  Music Projects ({len(files)}):")
    print(f"  {'='*40}\n")
    for f in sorted(files):
        name = f.replace(".yaml", "")
        proj = load_project(name)
        if proj:
            desc = proj.get("description", "")
            n_tracks = len(proj.get("tracks", []))
            n_prompts = len(proj.get("custom_prompts", []))
            print(f"  {name}")
            print(f"    {desc}")
            print(f"    {n_tracks} tracks, {n_prompts} custom prompts\n")


def cmd_show(name: str):
    proj = load_project(name)
    if not proj:
        print(f"  Project not found: {name}")
        print(f"  Available: {', '.join(f.replace('.yaml','') for f in os.listdir(PROJECTS_DIR) if f.endswith('.yaml'))}")
        return

    print(f"\n  Project: {proj.get('name', name)}")
    print(f"  {proj.get('description', '')}")
    print(f"  {'='*50}\n")

    # Target mood
    target = proj.get("target_mood", {})
    if target:
        print(f"  Target Mood:")
        for k, v in target.items():
            print(f"    {k}: {v}")
        print()

    # Tracks
    tracks = proj.get("tracks", [])
    if tracks:
        db = load_db()
        print(f"  Tracks ({len(tracks)}):")
        print(f"  {'-'*40}")
        for t in tracks:
            yt_id = t.get("youtube_id", "")
            title = t.get("title", "Unknown")
            role = t.get("role", "")
            # Look up from DB for metrics
            db_track = find_track(db, yt_id)
            if db_track:
                key = f"{db_track.get('key','')} {db_track.get('mode','')}".strip()
                bpm = db_track.get("bpm_feel") or db_track.get("bpm", "?")
                energy = db_track.get("energy")
                print(f"  {title}")
                print(f"    ID: {yt_id} | Key: {key} | BPM: {bpm} | E:{format_bar(energy)}")
                if role:
                    print(f"    Role: {role}")
            else:
                print(f"  {title} ({yt_id})")
                if role:
                    print(f"    Role: {role}")

            prompt = t.get("prompt", "")
            if prompt:
                print(f"    Prompt: {prompt[:80]}{'...' if len(prompt) > 80 else ''}")
            print()

    # Custom prompts
    prompts = proj.get("custom_prompts", [])
    if prompts:
        print(f"  Custom Prompts ({len(prompts)}):")
        print(f"  {'-'*40}")
        for p in prompts:
            print(f"  {p.get('name', 'Unnamed')}:")
            print(f"    {p.get('prompt', '')}")
            print()


def cmd_create(name: str):
    if load_project(name):
        print(f"  Project already exists: {name}")
        return

    project = {
        "name": name.replace("-", " ").replace("_", " ").title(),
        "description": "",
        "target_mood": {
            "energy": "0.3-0.7",
            "brightness": "0.1-0.3",
            "tempo": "moderate",
            "keywords": [],
        },
        "tracks": [],
        "custom_prompts": [],
    }
    save_project(name, project)
    print(f"  Created project: {name}")
    print(f"  Edit at: {os.path.join(PROJECTS_DIR, f'{name}.yaml')}")
    print(f"  Add tracks: python tools/music_project.py add {name} <youtube_id>")


def cmd_add(name: str, youtube_id: str, role: str = ""):
    proj = load_project(name)
    if not proj:
        print(f"  Project not found: {name}")
        return

    # Check if already in project
    for t in proj.get("tracks", []):
        if t.get("youtube_id") == youtube_id:
            print(f"  Track already in project: {youtube_id}")
            return

    # Look up in DB
    db = load_db()
    db_track = find_track(db, youtube_id)

    entry = {"youtube_id": youtube_id}
    if db_track:
        entry["title"] = db_track.get("title", "Unknown")
        entry["prompt"] = db_track.get("audial_prompt", "")
        print(f"  Adding: {entry['title']}")
    else:
        entry["title"] = "Unknown"
        entry["prompt"] = ""
        print(f"  Adding: {youtube_id} (not in database — run reference_track.py to analyze)")

    if role:
        entry["role"] = role

    if "tracks" not in proj:
        proj["tracks"] = []
    proj["tracks"].append(entry)
    save_project(name, proj)
    print(f"  Added to {name}. Total tracks: {len(proj['tracks'])}")


def cmd_remove(name: str, youtube_id: str):
    proj = load_project(name)
    if not proj:
        print(f"  Project not found: {name}")
        return

    tracks = proj.get("tracks", [])
    new_tracks = [t for t in tracks if t.get("youtube_id") != youtube_id]
    if len(new_tracks) == len(tracks):
        print(f"  Track not found in project: {youtube_id}")
        return

    proj["tracks"] = new_tracks
    save_project(name, proj)
    print(f"  Removed {youtube_id} from {name}. Remaining: {len(new_tracks)}")


def cmd_suggest(name: str):
    proj = load_project(name)
    if not proj:
        print(f"  Project not found: {name}")
        return

    target = proj.get("target_mood", {})
    keywords = target.get("keywords", [])
    existing_ids = {t.get("youtube_id") for t in proj.get("tracks", [])}

    db = load_db()
    if not db:
        print("  No tracks in database.")
        return

    # Score each track against target mood
    scored = []
    for track in db:
        if track.get("youtube_id") in existing_ids:
            continue

        score = 0.0

        # Keyword matching (search tags and prompt)
        tags = [t.lower() for t in (track.get("tags") or [])]
        prompt = (track.get("audial_prompt") or "").lower()
        for kw in keywords:
            kw_lower = kw.lower()
            if any(kw_lower in t for t in tags):
                score += 2.0
            elif kw_lower in prompt:
                score += 1.0

        # Energy range matching
        energy_range = target.get("energy", "")
        if isinstance(energy_range, str) and "-" in energy_range:
            try:
                lo, hi = map(float, energy_range.split("-"))
                e = track.get("energy")
                if e is not None:
                    if lo <= e <= hi:
                        score += 1.5
                    else:
                        score -= abs(e - (lo + hi) / 2)
            except (ValueError, TypeError):
                pass

        # Brightness range matching
        brightness_range = target.get("brightness", "")
        if isinstance(brightness_range, str) and "-" in brightness_range:
            try:
                lo, hi = map(float, brightness_range.split("-"))
                b = track.get("brightness")
                if b is not None:
                    if lo <= b <= hi:
                        score += 1.5
                    else:
                        score -= abs(b - (lo + hi) / 2)
            except (ValueError, TypeError):
                pass

        if score > 0:
            scored.append((score, track))

    scored.sort(key=lambda x: x[0], reverse=True)

    print(f"\n  Suggested tracks for: {proj.get('name', name)}")
    print(f"  Target: {', '.join(keywords)}")
    print(f"  {'='*50}\n")

    for score, t in scored[:10]:
        title = t.get("title", "Unknown")
        game = t.get("game", "")
        key = f"{t.get('key','')} {t.get('mode','')}".strip()
        bpm = t.get("bpm_feel") or t.get("bpm", "?")
        energy = t.get("energy")
        brightness = t.get("brightness")

        game_str = f" ({game})" if game else ""
        print(f"  {title}{game_str}  [score: {score:.1f}]")
        print(f"    Key: {key} | BPM: {bpm} | E:{format_bar(energy)} B:{format_bar(brightness)}")
        prompt = t.get("audial_prompt", "")
        if prompt:
            print(f"    Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
        print(f"    Add: python tools/music_project.py add {name} {t.get('youtube_id','')}")
        print()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "list":
        cmd_list()
    elif cmd == "show" and len(sys.argv) >= 3:
        cmd_show(sys.argv[2])
    elif cmd == "create" and len(sys.argv) >= 3:
        cmd_create(sys.argv[2])
    elif cmd == "add" and len(sys.argv) >= 4:
        role = ""
        if "--role" in sys.argv:
            idx = sys.argv.index("--role")
            if idx + 1 < len(sys.argv):
                role = sys.argv[idx + 1]
        cmd_add(sys.argv[2], sys.argv[3], role)
    elif cmd == "remove" and len(sys.argv) >= 4:
        cmd_remove(sys.argv[2], sys.argv[3])
    elif cmd == "suggest" and len(sys.argv) >= 3:
        cmd_suggest(sys.argv[2])
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
