"""Image resolution: pick a displayable image for each Exa result.

Strategy: use Exa's imageLinks/og image when present; otherwise fetch the
result page and scrape og:image / twitter:image. Results that still have no
image are dropped (the frontend also hides any card whose image 404s).
"""

import asyncio
import re
from urllib.parse import urljoin, urlparse

import httpx

from . import config

_OG_IMAGE_RE = re.compile(
    r'<meta[^>]+(?:property|name)=["\'](?:og:image|twitter:image)(?::src)?["\'][^>]+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
_OG_IMAGE_RE_REV = re.compile(
    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\'](?:og:image|twitter:image)(?::src)?["\']',
    re.IGNORECASE,
)

_VIDEO_RES = [
    re.compile(
        r'<meta[^>]+(?:property|name)=["\'](?:og:video(?::secure_url|:url)?|twitter:player:stream)["\'][^>]+content=["\']([^"\']+)["\']',
        re.IGNORECASE,
    ),
    re.compile(
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\'](?:og:video(?::secure_url|:url)?|twitter:player:stream)["\']',
        re.IGNORECASE,
    ),
    re.compile(r'<video[^>]+src=["\']([^"\']+\.mp4[^"\']*)["\']', re.IGNORECASE),
    re.compile(r'<source[^>]+src=["\']([^"\']+\.mp4[^"\']*)["\']', re.IGNORECASE),
]

_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif")


def source_domain(url: str) -> str:
    host = urlparse(url).netloc.lower()
    for domain in config.SEARCH_DOMAINS:
        if host == domain or host.endswith("." + domain):
            return domain
    return host.removeprefix("www.")


def is_gif(image_url: str) -> bool:
    return urlparse(image_url).path.lower().endswith(".gif")


def giphy_still(image_url: str) -> str | None:
    """Giphy serves a still-frame variant by suffixing the filename with _s."""
    if "giphy" not in image_url:
        return None
    path = urlparse(image_url).path.lower()
    if path.endswith(".gif") and not path.endswith("_s.gif"):
        return image_url[: image_url.rfind(".gif")] + "_s.gif"
    return None


def _pick_candidate(candidates: list[str]) -> str | None:
    for c in candidates:
        if c and c.startswith("http"):
            return c
    return None


async def _fetch_page(client: httpx.AsyncClient, page_url: str) -> str | None:
    try:
        resp = await client.get(
            page_url,
            headers={**config.BROWSER_HEADERS, "Accept": "text/html"},
            follow_redirects=True,
            timeout=8.0,
        )
    except (httpx.TimeoutException, httpx.TransportError):
        return None
    if resp.status_code != 200 or "text/html" not in resp.headers.get("content-type", ""):
        return None
    return resp.text[:300_000]


def parse_og_image(html: str, page_url: str) -> str | None:
    match = _OG_IMAGE_RE.search(html) or _OG_IMAGE_RE_REV.search(html)
    return urljoin(page_url, match.group(1)) if match else None


_VIDEO_EXTENSIONS = (".mp4", ".webm", ".m4v", ".mov")


def parse_video(html: str, page_url: str) -> str | None:
    for pattern in _VIDEO_RES:
        match = pattern.search(html)
        if match:
            url = urljoin(page_url, match.group(1))
            # Only direct video files. og:video often points at an HTML embed
            # page (e.g. player.vimeo.com/video/...), which can't play in a
            # <video> tag and gets rejected by the media proxy.
            if url.startswith("http") and urlparse(url).path.lower().endswith(_VIDEO_EXTENSIONS):
                return url
    return None


async def resolve_images(results: list[dict], media_type: str = "both") -> list[dict]:
    """Attach image_url / media / still_url to results; drop unresolvable ones."""
    semaphore = asyncio.Semaphore(8)

    async with httpx.AsyncClient() as client:

        async def resolve(result: dict) -> dict | None:
            domain = source_domain(result["url"])
            image_url = _pick_candidate(result.get("image_candidates", []))
            video_url = None

            if not image_url and urlparse(result["url"]).path.lower().endswith(_IMAGE_EXTENSIONS):
                # The page URL itself is a direct image link.
                image_url = result["url"]

            # Scrape the page when we still need an image, or when the source
            # hosts motion work behind a static poster (e.g. Dribbble mp4s).
            if not image_url or domain in config.VIDEO_SCRAPE_DOMAINS:
                async with semaphore:
                    html = await _fetch_page(client, result["url"])
                if html:
                    image_url = image_url or parse_og_image(html, result["url"])
                    if domain in config.VIDEO_SCRAPE_DOMAINS:
                        video_url = parse_video(html, result["url"])
            if not image_url:
                return None

            if video_url:
                media = "video"
            elif is_gif(image_url):
                media = "gif"
            else:
                media = "static"
            # "gif" filter means "things that move" — gifs and videos alike.
            if media_type == "static" and media != "static":
                return None
            if media_type == "gif" and media == "static":
                return None

            return {
                "id": result.get("exa_id") or result["url"],
                "url": result["url"],
                "title": result["title"],
                "image_url": image_url,
                "still_url": giphy_still(image_url),
                "video_url": video_url,
                "media": media,
                "source": domain,
                "score": result.get("score"),
            }

        resolved = await asyncio.gather(*(resolve(r) for r in results))

    return [r for r in resolved if r is not None]


def drop_generic_images(results: list[dict]) -> list[dict]:
    """Drop results that share an image URL with another result.

    When several different pages resolve to the same image, it's the site's
    generic og:image (e.g. the Dribbble logo), not content.
    """
    from collections import Counter

    counts = Counter(r["image_url"] for r in results)
    return [r for r in results if counts[r["image_url"]] == 1]


def interleave_by_source(results: list[dict]) -> list[dict]:
    """Round-robin results across source domains, preserving each source's
    own relevance order, so no single site dominates the top of the batch."""
    groups: dict[str, list[dict]] = {}
    order: list[str] = []
    for r in results:
        if r["source"] not in groups:
            groups[r["source"]] = []
            order.append(r["source"])
        groups[r["source"]].append(r)

    interleaved: list[dict] = []
    queues = [groups[s] for s in order]
    while queues:
        queues = [q for q in queues if q]
        for q in queues:
            if q:
                interleaved.append(q.pop(0))
    return interleaved


def cap_per_source(results: list[dict], cap: int, total: int) -> list[dict]:
    out: list[dict] = []
    counts: dict[str, int] = {}
    for r in results:
        if counts.get(r["source"], 0) >= cap:
            continue
        counts[r["source"]] = counts.get(r["source"], 0) + 1
        out.append(r)
        if len(out) >= total:
            break
    return out


def dedupe(results: list[dict], seen: set[str]) -> list[dict]:
    """Drop results whose page or image URL was already shown, plus in-batch dupes."""
    out = []
    batch_seen = set(seen)
    for r in results:
        keys = {r["url"], r["image_url"]}
        if keys & batch_seen:
            continue
        batch_seen |= keys
        out.append(r)
    return out
