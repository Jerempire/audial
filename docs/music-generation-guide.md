# Music Generation Guide for Art & Historical Projects

## Audial — Your Local Tool

Audial generates electronic/ambient music from text descriptions using AI + Strudel (a live-coding music language). You iterate on the sound in real-time, then export a WAV.

### Setup
1. `pnpm dev` → open `localhost:3000`
2. Settings (gear icon) → pick model → enter API key → save
3. Type a description → AI generates Strudel code → click Play
4. Iterate: "make it darker", "add reverb", "slower", etc.
5. Click `.wav` button → pick duration (15s–5m) → downloads a WAV file

### Keyboard Shortcuts
- **Space** — play/stop (when not typing in the input)
- **Ctrl+E** — export WAV (30s default)
- **Ctrl+Shift+N** — new song (clear everything)

### Preset Songs
Click any preset button (pink row) to instantly load an atmospheric composition — no API key needed. Available: Medieval Cathedral, Ancient Ruins, Renaissance Court, Gothic Horror, Impressionist Garden, War Drums.

### Dark Mode
Click the moon icon in the header to toggle dark mode. Preference is saved.

### Audial Prompt Examples (Art/Historical)

**Medieval / Dark Ages**
- "slow ambient drone with church organ texture, medieval, haunting"
- "dark monastic chant atmosphere, sparse bells, stone cathedral reverb"
- "medieval tavern, lute-like arpeggios, warm low drone, candlelit"

**Renaissance / Baroque**
- "dark atmospheric pad, Renaissance painting, candlelit, somber"
- "harpsichord-inspired arpeggios, baroque counterpoint, ornate, warm"
- "Renaissance court dance, gentle plucked strings, stately tempo"

**Ancient / Ruins**
- "ancient ruins ambient, wind textures, sparse percussion, mysterious"
- "Egyptian tomb atmosphere, deep drones, metallic resonance, vast space"
- "Greek temple, open fifths, slow strings, marble echo"

**Impressionist / Pastoral**
- "impressionist garden scene, soft arpeggios, warm pads, gentle"
- "watercolor landscape, flowing melodic fragments, piano-like, dreamy"
- "pastoral morning, birdsong textures, major key pads, light"

**Dark / Horror / Gothic**
- "gothic cathedral drone, deep organ, dissonant overtones, oppressive"
- "horror soundscape, creaking textures, sub-bass rumble, unsettling"
- "abandoned castle, wind through stone, distant metallic scrapes"

**War / Epic**
- "war drums, tribal percussion, building tension, brass-like synths"
- "battlefield aftermath, somber strings, sparse piano, mournful"
- "siege atmosphere, pounding low drums, horn calls, dust and chaos"

### What Audial Does Well
- Ambient pads, atmospheric drones, cinematic textures
- Dark/moody/historical-feeling soundscapes
- Electronic interpretations of emotional themes
- Iterative refinement — keep tweaking until it fits
- Long-form ambient (export up to 5 minutes)

### What Audial Doesn't Do
- Vocals or lyrics
- Realistic acoustic instrument recordings
- Polished radio-ready songs
- Specific melody recreation (can't hum it a tune)

---

## Other AI Music Platforms

### Suno — [suno.com](https://suno.com)
- **Best for**: Full songs with vocals, complete productions
- **How it works**: Text prompt → finished song (vocals, instruments, mixing)
- **Tracks up to**: 8 minutes
- **Pricing**: Free tier available, paid for more generations
- **Use case**: Background music for art presentations, exhibition soundtracks with vocals

### AIVA — [aiva.ai](https://www.aiva.ai)
- **Best for**: Orchestral and cinematic scores
- **How it works**: Choose style/mood → AI composes classical-style pieces
- **Use case**: Historical documentary scores, museum exhibit backgrounds, Renaissance-era evocations

### Beatoven.ai — [beatoven.ai](https://www.beatoven.ai)
- **Best for**: Video-synced music
- **How it works**: Upload video → AI shapes music around your edit cuts
- **Use case**: Art slideshow videos, exhibition walkthroughs with synchronized music

### Mubert — [mubert.com](https://mubert.com)
- **Best for**: Quick royalty-free ambient/instrumental tracks
- **How it works**: Short text prompt → instrumental track in ~10 seconds
- **Use case**: Fast background loops for digital art displays

### SOUNDRAW — [soundraw.io](https://soundraw.io)
- **Best for**: Fine-grained control over structure
- **How it works**: Generate → edit at the bar level, export stems
- **Use case**: When you need to precisely time music to visual sequences

---

## Reference Track Analyzer

Found a track on YouTube or Spotify that has the vibe you want? Analyze it and get an Audial prompt.

### Usage

```bash
# YouTube → analysis + Audial prompt
python tools/reference_track.py "https://youtube.com/watch?v=..."

# Keep the downloaded audio file
python tools/reference_track.py "https://youtube.com/watch?v=..." --keep

# Local file (mp3, wav, flac, etc.)
python tools/reference_track.py path/to/song.mp3
```

### What It Gives You
- **Key detection** — e.g., "C major (confidence: 0.86)"
- **Tempo** — BPM
- **Energy, brightness, density, rhythm** — 0–1 scale with visual bars
- **Track evolution** — how energy/brightness/key change over time (15s sections)
- **Ready-to-paste Audial prompt** — captures the vibe in one line

### Example Output
```
  Tempo:     117.5 BPM
  Key:       C major (confidence: 0.86)

  Energy       [####################] 1.00
  Brightness   [#######-------------] 0.38
  Density      [##############------] 0.74

  AUDIAL PROMPT:
  uplifting, intense, moderate tempo around 117 bpm, in C major, layered and dense
```

### Workflow: Recreate a Vibe
1. Find a YouTube track with the mood you want
2. `python tools/reference_track.py "URL"`
3. Copy the generated Audial prompt
4. Paste into Audial → AI generates a Strudel interpretation
5. Iterate: "more like the original but slower", "add the same kind of reverb", etc.

### Requirements
- `pip install yt-dlp librosa soundfile imageio-ffmpeg`

---

## Mood Analyzer (for your own exports)

Analyze any WAV file you've exported from Audial to understand its characteristics.

```bash
# Human-readable report
python tools/analyze_mood.py path/to/export.wav

# Machine-readable JSON
python tools/analyze_mood.py path/to/export.wav --json
```

Outputs key, tempo, energy, brightness, density, rhythm, mood tags, and suggested Audial prompts for adjustment.

---

## Copy for Claude (Feedback Loop)

Click the **"copy for claude"** button in Audial's controls to copy your current code + recent chat history. Paste it into Claude Code and describe what you hear — Claude reads the Strudel code and suggests changes.

---

## Choosing the Right Tool

| Scenario | Best Tool |
|---|---|
| Experimental ambient texture for a painting | **Audial** |
| Polished background song for an exhibition | **Suno** |
| Orchestral score for a historical video | **AIVA** |
| Quick ambient loop for a digital display | **Mubert** |
| Music synced to an art slideshow video | **Beatoven.ai** |
| Need stem exports for mixing | **SOUNDRAW** |
| Iterating on a specific sonic mood | **Audial** |

---

## Workflow: Art Project Soundtrack

1. **Find inspiration** — run `python tools/reference_track.py "YouTube URL"` on tracks with the right vibe
2. **Start in Audial** — paste the generated prompt, or try a preset, or describe from scratch
3. **Iterate** — refine through conversation ("more reverb", "add distant bells", "slower")
4. **Get feedback** — click "copy for claude" → paste in Claude Code → describe what you hear
5. **Analyze** — run `python tools/analyze_mood.py export.wav` to verify the mood matches your intent
6. **Export WAV** — download when it sounds right
7. **Optional**: Use Suno/AIVA for a polished companion track with real instrument sounds
8. **Layer** — combine Audial's textures with polished tracks in any audio editor (Audacity, etc.)
