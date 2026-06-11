"""PNG contact-sheet export of a board's selected images."""

import io

from PIL import Image, ImageDraw

from . import proxy

_COLS = 4
_CELL = 320
_GUTTER = 12
_HEADER = 72
_BG = (12, 12, 14)
_FG = (235, 235, 235)
_MUTED = (140, 140, 145)


async def render_contact_sheet(vibes: str, descriptors: list[str], image_urls: list[str]) -> bytes:
    tiles: list[Image.Image] = []
    for url in image_urls:
        try:
            data, _ = await proxy.fetch_image(url)
            img = Image.open(io.BytesIO(data)).convert("RGB")
        except Exception:
            continue
        # center-crop to square, then resize to cell size
        side = min(img.size)
        left = (img.width - side) // 2
        top = (img.height - side) // 2
        img = img.crop((left, top, left + side, top + side)).resize((_CELL, _CELL))
        tiles.append(img)

    if not tiles:
        raise ValueError("No images could be fetched for export.")

    cols = min(_COLS, len(tiles))
    rows = (len(tiles) + cols - 1) // cols
    width = _GUTTER + cols * (_CELL + _GUTTER)
    footer = 48 if descriptors else _GUTTER
    height = _HEADER + rows * (_CELL + _GUTTER) + footer

    sheet = Image.new("RGB", (width, height), _BG)
    draw = ImageDraw.Draw(sheet)
    draw.text((_GUTTER, 20), "MOODBOARD", fill=_MUTED)
    draw.text((_GUTTER, 40), vibes[:160], fill=_FG)

    for i, tile in enumerate(tiles):
        x = _GUTTER + (i % cols) * (_CELL + _GUTTER)
        y = _HEADER + (i // cols) * (_CELL + _GUTTER)
        sheet.paste(tile, (x, y))

    if descriptors:
        draw.text(
            (_GUTTER, height - 36),
            " · ".join(descriptors)[: width // 6],
            fill=_MUTED,
        )

    buf = io.BytesIO()
    sheet.save(buf, format="PNG")
    return buf.getvalue()
