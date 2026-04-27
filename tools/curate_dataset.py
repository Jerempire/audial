"""
Curate the song dataset: list, archive, restore, and preview entries.

Usage:
  python tools/curate_dataset.py list                    # list all songs with index numbers
  python tools/curate_dataset.py list --category sacred  # filter by genre/mood/title
  python tools/curate_dataset.py archive 5 12 23         # move entries to archive (by index)
  python tools/curate_dataset.py archive --title "Witch" # archive by title match
  python tools/curate_dataset.py restore 2               # restore from archive (by index)
  python tools/curate_dataset.py restore --all           # restore everything from archive
  python tools/curate_dataset.py stats                   # show dataset statistics
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SONG_INDEX_PATH = PROJECT_ROOT / "data" / "song-index.json"
ARCHIVE_PATH = PROJECT_ROOT / "data" / "archive" / "archived-songs.json"


def load_index() -> dict:
    with open(SONG_INDEX_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_index(data: dict):
    data["generated_at"] = datetime.now(timezone.utc).isoformat()
    with open(SONG_INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_archive() -> list[dict]:
    if ARCHIVE_PATH.exists():
        with open(ARCHIVE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_archive(songs: list[dict]):
    ARCHIVE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(ARCHIVE_PATH, "w", encoding="utf-8") as f:
        json.dump(songs, f, indent=2, ensure_ascii=False)


def cmd_list(args):
    index = load_index()
    songs = index["songs"]
    query = args.filter.lower() if args.filter else None

    print(f"Dataset: {len(songs)} songs\n")
    for i, s in enumerate(songs):
        searchable = f"{s['title']} {' '.join(s['genres'])} {' '.join(s['moods'])}".lower()
        if query and query not in searchable:
            continue
        bpm = f"{s['bpm']}bpm" if s.get("bpm") else "?"
        snippet_len = len(s.get("snippet", ""))
        print(f"  [{i:2d}] {s['title']}")
        print(f"       genres: {', '.join(s['genres'])}  moods: {', '.join(s['moods'])}  {bpm}  ({snippet_len} chars)")


def cmd_archive(args):
    index = load_index()
    archive = load_archive()

    to_remove = set()

    # By index numbers
    if args.indices:
        for idx in args.indices:
            if 0 <= idx < len(index["songs"]):
                to_remove.add(idx)
            else:
                print(f"  SKIP: index {idx} out of range (0-{len(index['songs'])-1})")

    # By title match
    if args.title:
        query = args.title.lower()
        for i, s in enumerate(index["songs"]):
            if query in s["title"].lower():
                to_remove.add(i)

    if not to_remove:
        print("Nothing to archive.")
        return

    # Show what will be archived
    removed = []
    for idx in sorted(to_remove, reverse=True):
        song = index["songs"].pop(idx)
        song["_archived_at"] = datetime.now(timezone.utc).isoformat()
        removed.append(song)
        print(f"  Archived: [{idx}] {song['title']}")

    archive.extend(removed)
    save_index(index)
    save_archive(archive)
    print(f"\nArchived {len(removed)} songs. Dataset now has {len(index['songs'])} songs. Archive has {len(archive)} songs.")


def cmd_restore(args):
    index = load_index()
    archive = load_archive()

    if not archive:
        print("Archive is empty.")
        return

    if args.all:
        for s in archive:
            s.pop("_archived_at", None)
            index["songs"].append(s)
            print(f"  Restored: {s['title']}")
        restored_count = len(archive)
        archive = []
    elif args.indices:
        restored_count = 0
        for idx in sorted(args.indices, reverse=True):
            if 0 <= idx < len(archive):
                song = archive.pop(idx)
                song.pop("_archived_at", None)
                index["songs"].append(song)
                print(f"  Restored: {song['title']}")
                restored_count += 1
            else:
                print(f"  SKIP: archive index {idx} out of range (0-{len(archive)-1})")
    else:
        # List archive contents
        print(f"Archive: {len(archive)} songs\n")
        for i, s in enumerate(archive):
            print(f"  [{i:2d}] {s['title']} (archived: {s.get('_archived_at', '?')[:10]})")
        return

    save_index(index)
    save_archive(archive)
    print(f"\nRestored {restored_count} songs. Dataset now has {len(index['songs'])} songs. Archive has {len(archive)} songs.")


def cmd_stats(args):
    index = load_index()
    archive = load_archive()
    songs = index["songs"]

    print(f"Dataset: {len(songs)} songs")
    print(f"Archive: {len(archive)} songs")
    print(f"Version: {index.get('version', '?')}")
    print(f"Updated: {index.get('generated_at', '?')[:19]}")

    # Genre breakdown
    genres: dict[str, int] = {}
    for s in songs:
        for g in s["genres"]:
            genres[g] = genres.get(g, 0) + 1
    print(f"\nGenres ({len(genres)}):")
    for g, c in sorted(genres.items(), key=lambda x: -x[1]):
        print(f"  {g}: {c}")

    # BPM range
    bpms = [s["bpm"] for s in songs if s.get("bpm")]
    if bpms:
        print(f"\nBPM: {min(bpms)}-{max(bpms)}, median {sorted(bpms)[len(bpms)//2]}")


def main():
    parser = argparse.ArgumentParser(description="Curate Audial song dataset")
    sub = parser.add_subparsers(dest="command")

    p_list = sub.add_parser("list", help="List all songs")
    p_list.add_argument("filter", nargs="?", help="Filter by title/genre/mood")

    p_archive = sub.add_parser("archive", help="Move songs to archive")
    p_archive.add_argument("indices", nargs="*", type=int, help="Song indices to archive")
    p_archive.add_argument("--title", help="Archive by title match")

    p_restore = sub.add_parser("restore", help="Restore songs from archive")
    p_restore.add_argument("indices", nargs="*", type=int, help="Archive indices to restore")
    p_restore.add_argument("--all", action="store_true", help="Restore all archived songs")

    sub.add_parser("stats", help="Show dataset statistics")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    {"list": cmd_list, "archive": cmd_archive, "restore": cmd_restore, "stats": cmd_stats}[args.command](args)


if __name__ == "__main__":
    main()
