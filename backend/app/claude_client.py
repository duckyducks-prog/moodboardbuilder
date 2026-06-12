"""Claude vision call: describe the shared visual DNA of selected images."""

import base64
import io
import json

import anthropic
from PIL import Image

from . import config, proxy


class DescribeError(Exception):
    def __init__(self, message: str, status: int = 502):
        super().__init__(message)
        self.status = status


_STYLE_SCHEMA = {
    "type": "object",
    "properties": {
        "descriptors": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Short search-friendly phrases (2-4 words) capturing the shared style.",
        },
        "palette": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Dominant shared colors as names or hex codes.",
        },
        "avoid": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Qualities clearly absent from or contrary to this style.",
        },
    },
    "required": ["descriptors", "palette", "avoid"],
    "additionalProperties": False,
}

_PROMPT = (
    "These images were hand-picked by a user as the closest matches to a visual "
    "style they are hunting for. Describe the shared visual DNA of these images: "
    "palette, lighting, texture, composition, era, medium, motion quality. "
    "Descriptors should be short, search-friendly phrases (2-4 words each) that "
    "would help find more imagery like this. The avoid list names qualities that "
    "are clearly absent or contrary to this style."
)

_MAX_EDGE = 768  # downscale before sending to keep vision token cost low


def _to_jpeg(data: bytes, max_edge: int = _MAX_EDGE) -> bytes:
    img = Image.open(io.BytesIO(data))
    img = img.convert("RGB")  # flattens GIFs to their first frame
    img.thumbnail((max_edge, max_edge))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


async def describe_images(image_urls: list[str]) -> dict:
    if not config.ANTHROPIC_API_KEY:
        raise DescribeError("ANTHROPIC_API_KEY is not set on the server.", status=503)

    blocks = []
    for url in image_urls:
        try:
            data, _ = await proxy.fetch_image(url)
            jpeg = _to_jpeg(data)
        except Exception:
            continue  # skip images that won't fetch/decode; describe the rest
        blocks.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": base64.standard_b64encode(jpeg).decode(),
                },
            }
        )

    if not blocks:
        raise DescribeError("None of the selected images could be fetched.", status=502)

    client = anthropic.AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)
    try:
        response = await client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=16000,
            thinking={"type": "adaptive"},
            messages=[{"role": "user", "content": blocks + [{"type": "text", "text": _PROMPT}]}],
            output_config={
                "format": {"type": "json_schema", "schema": _STYLE_SCHEMA},
            },
        )
    except anthropic.RateLimitError as exc:
        raise DescribeError(f"Anthropic rate limit: {exc.message}", status=429)
    except anthropic.APIStatusError as exc:
        raise DescribeError(f"Anthropic API error: {exc.message}", status=502)
    except anthropic.APIConnectionError:
        raise DescribeError("Could not reach the Anthropic API.", status=504)

    if response.stop_reason == "refusal":
        raise DescribeError("The model declined to describe these images.", status=502)

    text = next((b.text for b in response.content if b.type == "text"), None)
    if not text:
        raise DescribeError("Empty response from the model.", status=502)
    return json.loads(text)


# ---------------------------------------------------------------------------
# Quality gate: filter junk images out of a result batch before display.
# ---------------------------------------------------------------------------

_FILTER_SCHEMA = {
    "type": "object",
    "properties": {
        "keep": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "index": {"type": "integer"},
                    "relevance": {
                        "type": "integer",
                        "description": "0-10, how well this image serves the query as a visual reference.",
                    },
                },
                "required": ["index", "relevance"],
                "additionalProperties": False,
            },
            "description": "Usable images with their relevance scores.",
        },
    },
    "required": ["keep"],
    "additionalProperties": False,
}

_FILTER_PROMPT = (
    "You are quality-filtering image search results for the query: {query!r}.\n"
    "Each image above is labeled with an index. Decide for each whether it is a "
    "usable visual reference for a moodboard built around that query.\n"
    "REJECT (omit from keep): website logos and brand marks of the source sites "
    "themselves (the Dribbble basketball, Behance/Pinterest/Giphy logos), "
    "placeholder or error images, login/signup walls, user avatars and profile "
    "photos, blank or near-blank frames, screenshots of webpage chrome or cookie "
    "banners, and images completely unrelated to the query.\n"
    "KEEP everything else, including loosely related imagery — this is a "
    "creative reference hunt, so err on the side of keeping anything visually "
    "interesting and on-theme.\n"
    "For each kept image, also rate its relevance to the query from 0 to 10 "
    "(10 = exactly the brief: subject, technique, and mood all match; "
    "5 = right mood or technique but different subject; "
    "1-2 = only loosely adjacent)."
)


async def filter_results(query: str, results: list[dict]) -> list[dict]:
    """Fetch every candidate image and reject junk via one Claude vision call.

    Fails open: results whose images fetch successfully are returned even if
    the model call is unavailable (no key) or errors. Results whose images
    cannot be fetched are always dropped — they could never render anyway.
    The fetch pass also warms the proxy cache, so the browser loads instantly.
    """
    fetched: list[tuple[dict, bytes]] = []

    async def grab(result: dict):
        try:
            data, _ = await proxy.fetch_image(result["image_url"])
            fetched.append((result, _to_jpeg(data, config.VALIDATE_MAX_EDGE)))
        except Exception:
            pass  # unfetchable/undecodable -> drop

    import asyncio

    semaphore = asyncio.Semaphore(10)

    async def bounded(result: dict):
        async with semaphore:
            await grab(result)

    await asyncio.gather(*(bounded(r) for r in results))
    # restore original (relevance) order — gather appends as tasks finish
    order = {r["id"]: i for i, r in enumerate(results)}
    fetched.sort(key=lambda pair: order[pair[0]["id"]])

    if not config.ANTHROPIC_API_KEY or not fetched:
        return [r for r, _ in fetched]

    blocks = []
    for i, (_, jpeg) in enumerate(fetched):
        blocks.append({"type": "text", "text": f"Image {i}:"})
        blocks.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": base64.standard_b64encode(jpeg).decode(),
                },
            }
        )
    blocks.append({"type": "text", "text": _FILTER_PROMPT.format(query=query)})

    client = anthropic.AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)
    try:
        response = await client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=16000,
            thinking={"type": "adaptive"},
            messages=[{"role": "user", "content": blocks}],
            output_config={"format": {"type": "json_schema", "schema": _FILTER_SCHEMA}},
        )
        if response.stop_reason == "refusal":
            return [r for r, _ in fetched]
        text = next((b.text for b in response.content if b.type == "text"), "")
        keep = {
            entry["index"]: entry["relevance"]
            for entry in json.loads(text)["keep"]
            if isinstance(entry.get("index"), int)
        }
    except Exception:
        return [r for r, _ in fetched]  # fail open

    kept = []
    for i, (r, _) in enumerate(fetched):
        if i in keep:
            r["relevance"] = keep[i]
            kept.append(r)
    # most relevant first; stable, so the source interleave breaks ties
    kept.sort(key=lambda r: -r.get("relevance", 0))
    return kept
