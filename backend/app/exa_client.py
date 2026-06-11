"""Thin async client for the Exa.ai search API with retry/backoff."""

import asyncio

import httpx

from . import config


class ExaError(Exception):
    def __init__(self, message: str, status: int = 502):
        super().__init__(message)
        self.status = status


_RETRYABLE_STATUS = {429, 500, 502, 503, 529}
_MAX_ATTEMPTS = 3


async def _post(path: str, payload: dict) -> dict:
    if not config.EXA_API_KEY:
        raise ExaError("EXA_API_KEY is not set on the server.", status=503)

    headers = {"x-api-key": config.EXA_API_KEY, "content-type": "application/json"}
    last_error: Exception | None = None

    async with httpx.AsyncClient(timeout=30.0) as client:
        for attempt in range(_MAX_ATTEMPTS):
            try:
                resp = await client.post(f"{config.EXA_BASE_URL}{path}", json=payload, headers=headers)
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_error = exc
            else:
                if resp.status_code == 200:
                    return resp.json()
                if resp.status_code in _RETRYABLE_STATUS:
                    last_error = ExaError(
                        f"Exa returned {resp.status_code}: {resp.text[:200]}",
                        status=429 if resp.status_code == 429 else 502,
                    )
                else:
                    raise ExaError(f"Exa returned {resp.status_code}: {resp.text[:200]}", status=502)
            if attempt < _MAX_ATTEMPTS - 1:
                await asyncio.sleep(2 ** attempt)

    if isinstance(last_error, ExaError):
        raise last_error
    raise ExaError(f"Exa request failed: {last_error}", status=504)


def _contents_block() -> dict:
    # Ask Exa for image links so results resolve to displayable images,
    # not just page links. og:image scraping is the fallback (see images.py).
    return {"extras": {"imageLinks": 4}}


def _normalize(raw_results: list[dict]) -> list[dict]:
    results = []
    for r in raw_results:
        url = r.get("url")
        if not url:
            continue
        candidates = []
        if r.get("image"):
            candidates.append(r["image"])
        extras = r.get("extras") or {}
        candidates.extend(extras.get("imageLinks") or [])
        results.append(
            {
                "exa_id": r.get("id"),
                "url": url,
                "title": r.get("title") or "",
                "image_candidates": candidates,
            }
        )
    return results


async def search(query: str, num_results: int, domains: list[str]) -> list[dict]:
    payload = {
        "query": query,
        "type": "neural",
        "numResults": num_results,
        "includeDomains": domains,
        "contents": _contents_block(),
    }
    data = await _post("/search", payload)
    return _normalize(data.get("results", []))


async def find_similar(url: str, num_results: int, domains: list[str]) -> list[dict]:
    payload = {
        "url": url,
        "numResults": num_results,
        "includeDomains": domains,
        "contents": _contents_block(),
    }
    data = await _post("/findSimilar", payload)
    return _normalize(data.get("results", []))


async def find_similar_many(urls: list[str], num_results: int, domains: list[str]) -> list[dict]:
    """Run findSimilar for each selected URL in parallel and concatenate.

    A single failing findSimilar call shouldn't sink the whole refine round —
    failures are dropped as long as at least one source succeeds.
    """
    tasks = [find_similar(u, num_results, domains) for u in urls]
    outcomes = await asyncio.gather(*tasks, return_exceptions=True)
    merged: list[dict] = []
    errors: list[Exception] = []
    for outcome in outcomes:
        if isinstance(outcome, Exception):
            errors.append(outcome)
        else:
            merged.extend(outcome)
    if errors and not merged and len(errors) == len(tasks):
        raise errors[0]
    return merged
