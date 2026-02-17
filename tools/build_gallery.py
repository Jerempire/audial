"""
Build a reference track gallery HTML from tracks.json.

Generates a browsable, filterable gallery of all 148+ analyzed reference tracks
with YouTube thumbnails, audio characteristics, mood tags, and copyable Audial prompts.

Usage:
    python tools/build_gallery.py
"""
import json
import html
import math
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

BASE = Path(__file__).parent.parent


def load_tracks():
    """Load tracks from data/tracks.json."""
    with open(BASE / "data" / "tracks.json", encoding="utf-8") as f:
        data = json.load(f)
    return data["tracks"]


def clean_category(cat):
    """Normalize empty/missing categories."""
    if not cat or not cat.strip():
        return "Other"
    return cat.strip()


def get_game_label(track):
    """Get a display label for the game/source."""
    game = track.get("game", "")
    if game:
        return game
    return ""


def build_filters(tracks):
    """Extract category and tag distributions for filter UI."""
    categories = {}
    tags = {}
    games = {}

    for t in tracks:
        cat = clean_category(t.get("category", ""))
        categories[cat] = categories.get(cat, 0) + 1

        game = t.get("game", "")
        if game:
            games[game] = games.get(game, 0) + 1

        for tag in t.get("tags", []):
            tags[tag] = tags.get(tag, 0) + 1

    sorted_cats = sorted(categories.items(), key=lambda x: -x[1])
    # Top tags with 5+ occurrences for filter pills
    sorted_tags = [(t, n) for t, n in sorted(tags.items(), key=lambda x: -x[1]) if n >= 5]

    return sorted_cats, sorted_tags


def energy_color(val):
    """Color gradient for energy: blue(low) -> green(mid) -> orange(high) -> red(max)."""
    if val is None:
        return "#333"
    if val < 0.3:
        return "#4a9eff"
    elif val < 0.5:
        return "#4acea0"
    elif val < 0.7:
        return "#8ac44a"
    elif val < 0.85:
        return "#e8a840"
    else:
        return "#e85040"


def bar_width(val):
    """Convert 0-1 value to percentage width."""
    if val is None:
        return 0
    return max(4, round(val * 100))


def mode_color(mode):
    """Color for major/minor mode indicator."""
    if mode == "major":
        return "#e8c547"
    elif mode == "minor":
        return "#7b8adb"
    return "#666"


def generate_html(tracks, categories, top_tags):
    """Generate the full gallery HTML."""
    total = len(tracks)

    # Sort tracks: by category, then by game, then by title
    sorted_tracks = sorted(
        tracks,
        key=lambda t: (
            clean_category(t.get("category", "")),
            t.get("game", ""),
            t.get("title", ""),
        ),
    )

    # Category filter buttons
    cat_buttons = [
        f'<button class="cat-btn active" data-cat="all">All ({total})</button>'
    ]
    for cat, count in categories:
        safe = html.escape(cat)
        cat_buttons.append(
            f'<button class="cat-btn" data-cat="{safe}">{safe} ({count})</button>'
        )

    # Mode filter buttons
    n_major = sum(1 for t in tracks if t.get("mode") == "major")
    n_minor = sum(1 for t in tracks if t.get("mode") == "minor")

    # Tag filter buttons (top mood tags)
    tag_buttons = []
    for tag, count in top_tags:
        safe = html.escape(tag)
        tag_buttons.append(
            f'<button class="tag-btn" data-tag="{safe}">{safe} ({count})</button>'
        )

    # Build cards
    cards = []
    for t in sorted_tracks:
        title = html.escape(t.get("title", "Untitled"))
        game = html.escape(get_game_label(t))
        cat = html.escape(clean_category(t.get("category", "")))
        yt_id = html.escape(t.get("youtube_id", ""))
        key = html.escape(t.get("key", "?"))
        mode = t.get("mode", "")
        mode_label = html.escape(mode) if mode else ""
        bpm = t.get("bpm")
        bpm_feel = t.get("bpm_feel")
        energy = t.get("energy")
        brightness = t.get("brightness")
        density = t.get("density")
        prompt = html.escape(t.get("audial_prompt", ""), quote=True)
        tags = t.get("tags", [])
        notes = t.get("notes") or ""

        # Display BPM (prefer bpm_feel if different from bpm)
        if bpm_feel and bpm_feel != bpm:
            bpm_display = f"{int(bpm_feel)} <span class='bpm-actual'>(actual {int(bpm)})</span>"
        elif bpm:
            bpm_display = str(int(bpm))
        else:
            bpm_display = "?"

        # YouTube thumbnail
        thumb_url = f"https://img.youtube.com/vi/{yt_id}/mqdefault.jpg" if yt_id else ""
        yt_link = f"https://www.youtube.com/watch?v={yt_id}" if yt_id else "#"

        # Tags HTML
        tag_html = "".join(
            f'<span class="tag">{html.escape(tag)}</span>' for tag in tags
        )

        # Search data: title, game, category, tags, key, prompt
        search_parts = [title, game, cat, key, mode_label]
        search_parts.extend(html.escape(tag) for tag in tags)
        search_data = html.escape(" ".join(search_parts))

        # Tags as data attribute for filtering
        tags_data = html.escape(",".join(tags))

        # Metric bars
        def metric_bar(label, val, color):
            if val is None:
                return f"""<div class="metric">
              <span class="metric-label">{label}</span>
              <div class="metric-bar-bg"><div class="metric-bar" style="width:0%;background:#333"></div></div>
              <span class="metric-val">-</span>
            </div>"""
            pct = bar_width(val)
            return f"""<div class="metric">
              <span class="metric-label">{label}</span>
              <div class="metric-bar-bg"><div class="metric-bar" style="width:{pct}%;background:{color}"></div></div>
              <span class="metric-val">{val:.2f}</span>
            </div>"""

        energy_bar = metric_bar("Energy", energy, energy_color(energy))
        bright_bar = metric_bar("Bright", brightness, "#e8c547" if brightness and brightness > 0.4 else "#7b8adb")
        dense_bar = metric_bar("Dense", density, "#a87bdb" if density and density > 0.5 else "#5aaa8a")

        cards.append(f"""<div class="card" data-search="{search_data}" data-cat="{cat}" data-mode="{html.escape(mode)}" data-tags="{tags_data}" data-bpm="{bpm or 0}" data-energy="{energy or 0}">
  <a href="{yt_link}" target="_blank" class="card-thumb">
    <img src="{thumb_url}" loading="lazy" alt="{title}">
    <div class="play-icon">&#9654;</div>
  </a>
  <div class="card-info">
    <div class="card-header">
      <div class="card-title">{title}</div>
      {f'<div class="card-game">{game}</div>' if game else ''}
    </div>
    <div class="badges">
      <span class="badge key-badge" style="border-color:{mode_color(mode)}">{key} {mode_label}</span>
      <span class="badge bpm-badge">{bpm_display} BPM</span>
    </div>
    <div class="metrics">
      {energy_bar}
      {bright_bar}
      {dense_bar}
    </div>
    <div class="card-tags">{tag_html}</div>
    <button class="copy-btn" onclick="copyPrompt(this, `{prompt}`)">Copy Prompt</button>
  </div>
</div>""")

    cards_html = "\n".join(cards)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Audial Reference Track Gallery</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #0a0a0a; color: #e0e0e0; padding: 20px;
  min-height: 100vh;
}}

/* Header */
h1 {{ text-align: center; margin: 20px 0 6px; font-size: 1.8em; color: #f0f0f0; letter-spacing: -0.02em; }}
.subtitle {{ text-align: center; margin-bottom: 20px; color: #555; font-size: 13px; }}
.subtitle span {{ color: #666; }}

/* Search */
.search-bar {{ max-width: 1400px; margin: 0 auto 14px; }}
.search-bar input {{
  width: 100%; padding: 12px 20px; border: 1px solid #222; border-radius: 10px;
  background: #111; color: #fff; font-size: 14px; outline: none; transition: border-color 0.2s;
}}
.search-bar input:focus {{ border-color: #444; }}
.search-bar input::placeholder {{ color: #444; }}

/* Filter sections */
.filter-section {{
  max-width: 1400px; margin: 0 auto 10px;
  padding: 10px 14px; background: #111; border-radius: 10px;
}}
.filter-label {{
  font-size: 11px; color: #555; text-transform: uppercase; letter-spacing: 0.05em;
  margin-bottom: 6px; font-weight: 600;
}}
.filter-row {{ display: flex; flex-wrap: wrap; gap: 5px; }}

/* Category buttons */
.cat-btn, .tag-btn, .mode-btn, .sort-btn {{
  padding: 5px 12px; border: 1px solid #222; border-radius: 16px;
  background: transparent; color: #666; font-size: 12px; cursor: pointer;
  transition: all 0.15s; white-space: nowrap;
}}
.cat-btn:hover, .tag-btn:hover, .mode-btn:hover {{ border-color: #444; color: #999; }}
.cat-btn.active {{ background: #fff; color: #000; border-color: #fff; }}
.tag-btn.active {{ background: #7b8adb; color: #fff; border-color: #7b8adb; }}
.mode-btn.active {{ background: #e8c547; color: #000; border-color: #e8c547; }}

/* Sort controls */
.controls-row {{
  max-width: 1400px; margin: 0 auto 12px;
  display: flex; justify-content: space-between; align-items: center;
  padding: 0 4px;
}}
.sort-group {{ display: flex; gap: 5px; align-items: center; }}
.sort-label {{ font-size: 11px; color: #444; margin-right: 4px; }}
.sort-btn.active {{ background: #333; color: #ccc; border-color: #444; }}

/* Count */
.filter-count {{ font-size: 12px; color: #444; }}

/* Grid */
.grid {{
  display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 14px; max-width: 1400px; margin: 0 auto;
}}

/* Card */
.card {{
  background: #131313; border-radius: 10px; overflow: hidden;
  border: 1px solid #1a1a1a; transition: transform 0.2s, box-shadow 0.2s;
}}
.card:hover {{ transform: translateY(-2px); box-shadow: 0 8px 24px rgba(255,255,255,0.04); border-color: #252525; }}
.card.hidden {{ display: none; }}

/* Thumbnail */
.card-thumb {{
  position: relative; display: block; overflow: hidden;
  aspect-ratio: 16/9; background: #0a0a0a;
}}
.card-thumb img {{ width: 100%; height: 100%; object-fit: cover; display: block; transition: opacity 0.2s; }}
.card-thumb:hover img {{ opacity: 0.8; }}
.play-icon {{
  position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
  font-size: 28px; color: rgba(255,255,255,0.7); opacity: 0;
  transition: opacity 0.2s; pointer-events: none;
  text-shadow: 0 2px 8px rgba(0,0,0,0.6);
}}
.card-thumb:hover .play-icon {{ opacity: 1; }}

/* Card info */
.card-info {{ padding: 12px 14px 14px; }}
.card-header {{ margin-bottom: 8px; }}
.card-title {{
  font-size: 14px; font-weight: 600; color: #eee;
  line-height: 1.3; margin-bottom: 2px;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}}
.card-game {{ font-size: 12px; color: #666; }}

/* Badges */
.badges {{ display: flex; gap: 6px; margin-bottom: 8px; flex-wrap: wrap; }}
.badge {{
  font-size: 11px; padding: 2px 8px; border-radius: 4px;
  background: #1a1a1a; border: 1px solid #252525;
}}
.key-badge {{ font-weight: 600; border-width: 1.5px; }}
.bpm-badge {{ color: #999; }}
.bpm-actual {{ color: #555; font-size: 10px; }}

/* Metrics */
.metrics {{ margin-bottom: 8px; }}
.metric {{ display: flex; align-items: center; gap: 6px; margin-bottom: 3px; }}
.metric-label {{ font-size: 10px; color: #555; width: 40px; text-align: right; flex-shrink: 0; }}
.metric-bar-bg {{ flex: 1; height: 6px; background: #1a1a1a; border-radius: 3px; overflow: hidden; }}
.metric-bar {{ height: 100%; border-radius: 3px; transition: width 0.3s ease; }}
.metric-val {{ font-size: 10px; color: #555; width: 30px; font-family: 'SF Mono', 'Cascadia Code', monospace; }}

/* Tags */
.card-tags {{ display: flex; flex-wrap: wrap; gap: 3px; margin-bottom: 8px; }}
.tag {{
  background: #1a1a1a; color: #777; padding: 2px 7px; border-radius: 4px;
  font-size: 10px; border: 1px solid #222;
}}

/* Copy button */
.copy-btn {{
  width: 100%; padding: 6px; border: 1px solid #222; border-radius: 6px;
  background: #161616; color: #888; font-size: 12px; cursor: pointer;
  transition: all 0.15s; font-weight: 500;
}}
.copy-btn:hover {{ background: #1e1e1e; color: #bbb; border-color: #333; }}
.copy-btn.copied {{ background: #1a2a1a; color: #5a5; border-color: #2a3a2a; }}

/* Toast notification */
.toast {{
  position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%) translateY(100px);
  background: #1a2a1a; color: #5a5; padding: 10px 24px; border-radius: 8px;
  font-size: 13px; border: 1px solid #2a3a2a; pointer-events: none;
  transition: transform 0.3s ease; z-index: 100;
}}
.toast.show {{ transform: translateX(-50%) translateY(0); }}

/* Responsive */
@media (max-width: 700px) {{
  .grid {{ grid-template-columns: 1fr; }}
  body {{ padding: 12px; }}
  h1 {{ font-size: 1.4em; }}
}}
</style>
</head>
<body>

<h1>Audial Reference Tracks</h1>
<div class="subtitle">
  {total} tracks <span>&middot;</span>
  {n_major} major <span>&middot;</span> {n_minor} minor <span>&middot;</span>
  BPM {int(min(t.get('bpm', 999) for t in tracks if t.get('bpm')))}&ndash;{int(max(t.get('bpm', 0) for t in tracks if t.get('bpm')))}
</div>

<div class="search-bar">
  <input type="text" id="search" placeholder="Search by title, game, tag, key...">
</div>

<div class="filter-section">
  <div class="filter-label">Category</div>
  <div class="filter-row" id="catBar">
    {"".join(cat_buttons)}
  </div>
</div>

<div class="filter-section">
  <div class="filter-label">Mood</div>
  <div class="filter-row" id="tagBar">
    {"".join(tag_buttons)}
  </div>
</div>

<div class="filter-section">
  <div class="filter-label">Mode</div>
  <div class="filter-row" id="modeBar">
    <button class="mode-btn active" data-mode="all">All</button>
    <button class="mode-btn" data-mode="major">Major ({n_major})</button>
    <button class="mode-btn" data-mode="minor">Minor ({n_minor})</button>
  </div>
</div>

<div class="controls-row">
  <div class="sort-group">
    <span class="sort-label">Sort:</span>
    <button class="sort-btn active" data-sort="default">Default</button>
    <button class="sort-btn" data-sort="bpm-asc">BPM &uarr;</button>
    <button class="sort-btn" data-sort="bpm-desc">BPM &darr;</button>
    <button class="sort-btn" data-sort="energy-desc">Energy &darr;</button>
    <button class="sort-btn" data-sort="energy-asc">Energy &uarr;</button>
    <button class="sort-btn" data-sort="alpha">A&ndash;Z</button>
  </div>
  <div class="filter-count" id="filterCount">Showing {total} of {total}</div>
</div>

<div class="grid" id="grid">
{cards_html}
</div>

<div class="toast" id="toast">Prompt copied to clipboard</div>

<script>
const grid = document.getElementById('grid');
const cards = [...document.querySelectorAll('.card')];
const searchInput = document.getElementById('search');
const filterCount = document.getElementById('filterCount');
const toast = document.getElementById('toast');
const total = {total};

let activeCat = 'all';
let activeMode = 'all';
let activeTags = new Set();
let searchTerm = '';
let currentSort = 'default';

// Store original order for default sort
const originalOrder = cards.map(c => c);

function matchesFilters(card) {{
  // Search
  if (searchTerm && !card.dataset.search.toLowerCase().includes(searchTerm)) return false;
  // Category
  if (activeCat !== 'all' && card.dataset.cat !== activeCat) return false;
  // Mode
  if (activeMode !== 'all' && card.dataset.mode !== activeMode) return false;
  // Tags (AND logic: card must have ALL selected tags)
  if (activeTags.size > 0) {{
    const cardTags = card.dataset.tags.split(',');
    for (const t of activeTags) {{
      if (!cardTags.includes(t)) return false;
    }}
  }}
  return true;
}}

function filterCards() {{
  let shown = 0;
  cards.forEach(card => {{
    if (matchesFilters(card)) {{
      card.classList.remove('hidden');
      shown++;
    }} else {{
      card.classList.add('hidden');
    }}
  }});
  filterCount.textContent = `Showing ${{shown}} of ${{total}}`;
}}

function sortCards() {{
  let order;
  switch (currentSort) {{
    case 'bpm-asc':
      order = [...cards].sort((a, b) => parseFloat(a.dataset.bpm) - parseFloat(b.dataset.bpm));
      break;
    case 'bpm-desc':
      order = [...cards].sort((a, b) => parseFloat(b.dataset.bpm) - parseFloat(a.dataset.bpm));
      break;
    case 'energy-desc':
      order = [...cards].sort((a, b) => parseFloat(b.dataset.energy) - parseFloat(a.dataset.energy));
      break;
    case 'energy-asc':
      order = [...cards].sort((a, b) => parseFloat(a.dataset.energy) - parseFloat(b.dataset.energy));
      break;
    case 'alpha':
      order = [...cards].sort((a, b) => {{
        const ta = a.querySelector('.card-title').textContent;
        const tb = b.querySelector('.card-title').textContent;
        return ta.localeCompare(tb);
      }});
      break;
    default:
      order = originalOrder;
  }}
  order.forEach(card => grid.appendChild(card));
  filterCards();
}}

// Search
searchInput.addEventListener('input', e => {{
  searchTerm = e.target.value.toLowerCase();
  filterCards();
}});

// Category filter
document.querySelectorAll('.cat-btn').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('.cat-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    activeCat = btn.dataset.cat;
    filterCards();
  }});
}});

// Mode filter
document.querySelectorAll('.mode-btn').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    activeMode = btn.dataset.mode;
    filterCards();
  }});
}});

// Tag filter (toggle, multi-select)
document.querySelectorAll('.tag-btn').forEach(btn => {{
  btn.addEventListener('click', () => {{
    const tag = btn.dataset.tag;
    if (activeTags.has(tag)) {{
      activeTags.delete(tag);
      btn.classList.remove('active');
    }} else {{
      activeTags.add(tag);
      btn.classList.add('active');
    }}
    filterCards();
  }});
}});

// Sort
document.querySelectorAll('.sort-btn').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('.sort-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentSort = btn.dataset.sort;
    sortCards();
  }});
}});

// Copy prompt
function copyPrompt(btn, text) {{
  navigator.clipboard.writeText(text);
  btn.textContent = 'Copied!';
  btn.classList.add('copied');
  toast.classList.add('show');
  setTimeout(() => {{ btn.textContent = 'Copy Prompt'; btn.classList.remove('copied'); }}, 1500);
  setTimeout(() => toast.classList.remove('show'), 2000);
}}
</script>
</body>
</html>"""


def main():
    tracks = load_tracks()
    categories, top_tags = build_filters(tracks)
    gallery_html = generate_html(tracks, categories, top_tags)

    out_path = BASE / "gallery" / "reference-tracks.html"
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(gallery_html)

    print(f"Built gallery: {out_path}")
    print(f"  Total tracks: {len(tracks)}")
    print(f"  Categories: {len(categories)}")
    print(f"  Top mood tags: {len(top_tags)}")


if __name__ == "__main__":
    main()
