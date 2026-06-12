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


async def _scrape_og_image(client: httpx.AsyncClient, page_url: str) -> str | None:
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
    head = resp.text[:200_000]
    match = _OG_IMAGE_RE.search(head) or _OG_IMAGE_RE_REV.search(head)
    if not match:
        return None
    return urljoin(page_url, match.group(1))


async def resolve_images(results: list[dict], media_type: str = "both") -> list[dict]:
    """Attach image_url / media / still_url to results; drop unresolvable ones."""
    semaphore = asyncio.Semaphore(8)

    async with httpx.AsyncClient() as client:

        async def resolve(result: dict) -> dict | None:
            image_url = _pick_candidate(result.get("image_candidates", []))
            if not image_url:
                # The page URL itself might be a direct image link.
                if urlparse(result["url"]).path.lower().endswith(_IMAGE_EXTENSIONS):
                    image_url = result["url"]
                else:
                    async with semaphore:
                        image_url = await _scrape_og_image(client, result["url"])
            if not image_url:
                return None

            media = "gif" if is_gif(image_url) else "static"
            if media_type != "both" and media != media_type:
                return None

            return {
                "id": result.get("exa_id") or result["url"],
                "url": result["url"],
                "title": result["title"],
                "image_url": image_url,
                "still_url": giphy_still(image_url),
                "media": media,
                "source": source_domain(result["url"]),
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
