# Moodboard Builder

An iterative vibes-to-visuals search tool for creative direction, modeled on
Midjourney's style-tuner loop — but for found imagery.

Type freeform **vibes** ("sun-bleached 16mm nostalgia, coastal Brazil, slow
zooms, grain"), get a masonry grid of 10–15 images/GIFs/film stills pulled
from visual reference sites, select the 3–5 closest to your intent, and
**refine**. Each refinement round combines:

1. **Exa `findSimilar`** on the pages of your selected images, and
2. a fresh **Exa neural search** using your original vibes enriched with an
   accumulating **style profile** — descriptors extracted by Claude (vision)
   from your selected images each round.

Selections compound across rounds into a final moodboard you can export as a
PNG contact sheet or JSON, and share via a read-only link.

## Stack

- **Backend** — FastAPI (Python), SQLite, Exa.ai search, Anthropic API
  (Claude vision with structured outputs). All API keys stay server-side.
- **Frontend** — React + Vite + Tailwind. Dark, image-forward UI.

## Running it

```sh
export EXA_API_KEY=...        # required for search
export ANTHROPIC_API_KEY=...  # required for style-profile extraction

# backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --port 8000 --reload

# frontend (dev, separate terminal)
cd frontend
npm install
npm run dev          # http://localhost:5173 (proxies /api to :8000)
```

For a single-server setup, `npm run build` in `frontend/` — the backend
serves `frontend/dist/` (including the `/board/:id` share route) at
`http://localhost:8000`.

Missing keys degrade gracefully: search returns a clear error toast without
`EXA_API_KEY`; without `ANTHROPIC_API_KEY` the refine loop still works, it
just skips style-profile extraction for that round.

## How it works

| Endpoint | Purpose |
|---|---|
| `POST /api/search` | Creates a board + round 1. Over-fetches ~25 Exa results (`type: neural`, `includeDomains`, `contents.extras.imageLinks`), resolves each to a displayable image (Exa image links → og:image scrape fallback), filters by media type, dedupes, caps at 15. |
| `POST /api/describe` | Sends the selected images to Claude (`claude-opus-4-8`, vision + JSON-schema structured output) → `{descriptors, palette, avoid}`. |
| `POST /api/refine` | Records selections, persists the style profile, runs `findSimilar` per selected URL **plus** an enriched search, merges, and dedupes against everything already shown on the board. |
| `GET /api/board/:id` | Full board state — also powers the read-only share link `/board/:id`. |
| `GET /api/board/:id/export.png` | PNG contact sheet (Pillow). |
| `GET /api/board/:id/export.json` | Image URLs + style profile. |
| `GET /api/img?url=` | Caching image proxy (Pinterest & friends block hotlinking). Image content-types only; private/loopback hosts rejected. |

### Tuning

- **Sources**: edit `SEARCH_DOMAINS` in `backend/app/config.py` — one list,
  used for search, refine, and the frontend's source-filter chips.
- **Batch sizes**: `OVERFETCH_COUNT`, `MAX_RESULTS_PER_ROUND`,
  `FIND_SIMILAR_PER_SELECTION` in the same file.

### Behavior notes

- **Dedupe**: an image is never shown twice on the same board — page *and*
  image URLs from every prior round are excluded.
- **Style profile chips** are removable in the UI; pruned descriptors are
  excluded from the next round's enriched query.
- **Round rail**: jump back to any round and re-branch from a different
  selection set — rounds form a tree (`parent_round_id`).
- **GIF perf**: Giphy results get a still thumbnail; the "GIFs on hover only"
  toggle keeps the grid light. Exa rate limits/timeouts retry with backoff
  (3 attempts) and surface as toasts.
- Cards whose image fails to load through the proxy hide themselves, so the
  grid stays clean even when a CDN refuses us.
