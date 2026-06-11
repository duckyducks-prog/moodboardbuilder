import os

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# Search sources — edit this list to add/remove visual reference sites.
# ---------------------------------------------------------------------------
SEARCH_DOMAINS = [
    "dribbble.com",
    "pinterest.com",
    "film-grab.com",
    "behance.net",
    "giphy.com",
]

# API keys (server-side only — never exposed to the frontend)
EXA_API_KEY = os.environ.get("EXA_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

EXA_BASE_URL = "https://api.exa.ai"

# Over-fetch from Exa so that enough clean cards survive image validation.
OVERFETCH_COUNT = 40
MAX_RESULTS_PER_ROUND = 30
FIND_SIMILAR_PER_SELECTION = 8
# findSimilar fan-out cap: with unlimited selections, only the first N
# selected pages seed findSimilar calls (cost/latency control).
MAX_FIND_SIMILAR_SEEDS = 8
# Images sent to Claude for style analysis (vision cost control).
MAX_DESCRIBE_IMAGES = 8
# Exa caps numResults; used when growing requests to skip past seen results.
EXA_MAX_RESULTS = 100

CLAUDE_MODEL = "claude-opus-4-8"

DB_PATH = os.environ.get("MOODBOARD_DB", os.path.join(_BACKEND_DIR, "moodboard.db"))

# Image proxy cache
IMG_CACHE_DIR = os.path.join(_BACKEND_DIR, ".cache", "img")
IMG_MAX_BYTES = 15 * 1024 * 1024  # refuse to proxy images larger than this
IMG_FETCH_TIMEOUT = 15.0

# Headers used when fetching pages/images so hotlink-hostile CDNs cooperate.
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
