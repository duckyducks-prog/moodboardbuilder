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


def _to_jpeg(data: bytes) -> bytes:
    img = Image.open(io.BytesIO(data))
    img = img.convert("RGB")  # flattens GIFs to their first frame
    img.thumbnail((_MAX_EDGE, _MAX_EDGE))
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
