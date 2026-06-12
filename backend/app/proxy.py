"""Image proxy with disk caching.

Pinterest and several CDNs block hotlinking, so the frontend loads every
image through GET /api/img?url=... . Only image content types are proxied,
and private/loopback hosts are rejected to prevent SSRF.
"""

import hashlib
import ipaddress
import json
import os
import socket
from urllib.parse import urlparse

import httpx

from . import config


class ProxyError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


def _is_safe_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return False
    try:
        infos = socket.getaddrinfo(parsed.hostname, None)
    except socket.gaierror:
        return False
    for info in infos:
        try:
            addr = ipaddress.ip_address(info[4][0])
        except ValueError:
            return False
        if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved:
            return False
    return True


def _cache_paths(url: str) -> tuple[str, str]:
    digest = hashlib.sha256(url.encode()).hexdigest()
    return (
        os.path.join(config.IMG_CACHE_DIR, digest + ".bin"),
        os.path.join(config.IMG_CACHE_DIR, digest + ".json"),
    )


def _read_cache(url: str) -> tuple[bytes, str] | None:
    body_path, meta_path = _cache_paths(url)
    if not (os.path.exists(body_path) and os.path.exists(meta_path)):
        return None
    try:
        with open(meta_path) as f:
            meta = json.load(f)
        with open(body_path, "rb") as f:
            return f.read(), meta["content_type"]
    except (OSError, KeyError, ValueError):
        return None


def _write_cache(url: str, body: bytes, content_type: str) -> None:
    os.makedirs(config.IMG_CACHE_DIR, exist_ok=True)
    body_path, meta_path = _cache_paths(url)
    try:
        with open(body_path, "wb") as f:
            f.write(body)
        with open(meta_path, "w") as f:
            json.dump({"content_type": content_type, "url": url}, f)
    except OSError:
        pass


async def fetch_image(url: str) -> tuple[bytes, str]:
    """Fetch an image with caching; returns (bytes, content_type)."""
    cached = _read_cache(url)
    if cached:
        return cached

    if not _is_safe_url(url):
        raise ProxyError("URL is not allowed.", status=400)

    parsed = urlparse(url)
    headers = {
        **config.BROWSER_HEADERS,
        # Some CDNs require a same-site referer.
        "Referer": f"{parsed.scheme}://{parsed.netloc}/",
    }
    try:
        async with httpx.AsyncClient(timeout=config.IMG_FETCH_TIMEOUT) as client:
            resp = await client.get(url, headers=headers, follow_redirects=True)
    except (httpx.TimeoutException, httpx.TransportError) as exc:
        raise ProxyError(f"Upstream fetch failed: {exc}", status=502)

    if resp.status_code != 200:
        raise ProxyError(f"Upstream returned {resp.status_code}.", status=502)

    content_type = resp.headers.get("content-type", "").split(";")[0].strip().lower()
    # Images plus short looping clips (Dribbble motion shots are mp4s).
    if not content_type.startswith(("image/", "video/")):
        raise ProxyError("URL did not resolve to an image or video.", status=415)
    if len(resp.content) > config.IMG_MAX_BYTES:
        raise ProxyError("File too large to proxy.", status=413)

    _write_cache(url, resp.content, content_type)
    return resp.content, content_type
