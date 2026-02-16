# Audial - Claude Code Project Notes

## What This Is
AI-powered music generator using Strudel (live coding language for music). Next.js app that takes text prompts and generates playable Strudel compositions via LLM.

## Architecture
- **Frontend**: Next.js 14 + React 18 + Tailwind + Strudel Web Components
- **AI Backend**: `app/api/claude/route.ts` — calls Claude/Gemini/OpenAI to generate Strudel code
- **System Prompt**: `lib/systemPrompt.ts` — musical taste framework + Strudel spec + output rules
- **Dataset/Retrieval**: `lib/dataset/` — fuzzy retrieval system that feeds reference songs to the LLM
  - `songIndex.ts` — loads song index from `data/song-index.json`
  - `stylePriors.ts` — loads style priors from `data/style-priors.json`
  - `retrieve.ts` — always-on fuzzy retrieval scoring with synonym expansion
  - `synonyms.ts` — prompt expansion map (genre synonyms, cultural terms)
- **Creative Directives**: `lib/creativeDirectives.ts` — builds user prompt with dataset references
- **Presets**: `lib/presets.ts` — 6 atmospheric preset compositions
- **Reference Tracks**: `data/tracks.json` — 148 analyzed reference tracks with metadata

## Dataset Pipeline
- `data/song-index.json` — SongIndexEntry objects with Strudel code snippets + metadata
- `data/style-priors.json` — derived composition guidelines (gain ranges, CPM distribution, etc.)
- `tools/build_dataset.py` — batch generates Strudel code from reference tracks via LLM API
- Retrieval is "always-on": every prompt gets top-k references + diverse exemplar

## Key Patterns
- **Output contract**: LLM must output ONLY Strudel code starting with `setcpm(`. No prose, no markdown.
- **Voice structure**: 3-6 voices using `$:` prefix. Bass + pad/chords + drums minimum.
- **Gain limits**: Never exceed 0.9. Typical ranges in style-priors.json.
- **Test suite**: `vitest` — 42 tests covering parseOutput, validateOutput, synonyms

## Commands
```bash
pnpm dev          # dev server
pnpm build        # production build
pnpm test         # run tests
pnpm check        # typecheck + test + build (all 3)
pnpm lint         # tsc --noEmit only
```

## Non-PHI
This is a personal creative project. Full autonomy — run scripts, iterate on output, test freely.
