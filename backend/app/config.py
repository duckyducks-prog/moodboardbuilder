import os

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# Search sources — edit this list to add/remove visual reference sites.
# ---------------------------------------------------------------------------
SEARCH_DOMAINS = [
    # design & motion
    "dribbble.com",
    "behance.net",
    "pinterest.com",
    "eyecannndy.com",
    "giphy.com",
    # film & commercial cinematography
    "film-grab.com",
    "shot.cafe",
    "frameset.app",
    "movie-screencaps.com",
    "evanerichards.com",
    "vimeo.com",
]

# API keys (server-side only — never exposed to the frontend)
EXA_API_KEY = os.environ.get("EXA_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

EXA_BASE_URL = "https://api.exa.ai"

# Over-fetch from Exa so that enough clean cards survive image validation.
OVERFETCH_COUNT = 60
MAX_RESULTS_PER_ROUND = 48
# No single source may fill more than this many cards in a round.
MAX_PER_DOMAIN = 10
FIND_SIMILAR_PER_SELECTION = 8
# findSimilar fan-out cap: with unlimited selections, only the first N
# selected pages seed findSimilar calls (cost/latency control).
MAX_FIND_SIMILAR_SEEDS = 8
# Images sent to Claude for style analysis (vision cost control).
MAX_DESCRIBE_IMAGES = 8
# Vision quality gate: candidate thumbnails are downscaled to this edge for
# the single junk-filter call (small = cheap; enough to spot logos/placeholders).
VALIDATE_MAX_EDGE = 384

# Domains whose result pages get scraped for an embedded video (mp4), so
# motion work plays in the grid instead of showing a static poster frame.
VIDEO_SCRAPE_DOMAINS = {"dribbble.com"}

# Default source bias per content type, used when the user hasn't picked
# sources explicitly. Giphy is deliberately NOT in the motion defaults —
# Dribbble/Behance/Pinterest carry better motion-design work; Giphy only
# joins in when the user filters to GIFs or picks it explicitly.
CONTENT_TYPE_DOMAINS = {
    "motion": ["dribbble.com", "behance.net", "pinterest.com", "eyecannndy.com"],
    "live": [
        "film-grab.com",
        "shot.cafe",
        "frameset.app",
        "movie-screencaps.com",
        "evanerichards.com",
        "pinterest.com",
        "vimeo.com",
    ],
    "both": SEARCH_DOMAINS,
}

# ---------------------------------------------------------------------------
# Per-source search strategy. Sources are not interchangeable: Vimeo needs
# semantic search (its titles/tags are weak signal), Giphy is tag-driven,
# and each source frames the query differently for live action vs motion.
# ---------------------------------------------------------------------------

# "inherit" follows the user's Vibes/Technical choice; explicit values pin it.
DOMAIN_SEARCH_TYPE = {
    "vimeo.com": "neural",      # always semantic — keyword search is too literal there
    "pinterest.com": "neural",  # board/pin discovery is semantic by nature
    "giphy.com": "keyword",     # pure tag search
    # everyone else: inherit
}

# Query hints per source and content type ("*" = any content type).
DOMAIN_HINTS = {
    "vimeo.com": {
        "live": "commercial short film cinematography",
        "motion": "motion design animation reel",
        "both": "commercial film",
    },
    "pinterest.com": {
        "live": "film still cinematography frame",
        "motion": "motion design animation",
        "both": "",
    },
    "dribbble.com": {"motion": "motion design animation", "*": ""},
    "behance.net": {"motion": "motion design", "*": ""},
    "film-grab.com": {"*": "film still"},
    "shot.cafe": {"*": "film still"},
    "frameset.app": {"*": "cinematography frame"},
    "movie-screencaps.com": {"*": "film frame"},
    "evanerichards.com": {"*": "cinematography"},
}


def domain_hint(domain: str, content_type: str) -> str:
    entry = DOMAIN_HINTS.get(domain, {})
    return entry.get(content_type, entry.get("*", ""))


def domain_search_type(domain: str, user_type: str) -> str:
    pinned = DOMAIN_SEARCH_TYPE.get(domain, "inherit")
    return user_type if pinned == "inherit" else pinned
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
