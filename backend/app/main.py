import os

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import claude_client, config, db, exa_client, export, images, proxy

app = FastAPI(title="Moodboard Builder")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

db.init_db()

MIN_SELECT = 3
MAX_SELECT = 5


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class SearchRequest(BaseModel):
    vibes: str = Field(min_length=2, max_length=2000)
    media_type: str = "both"  # static | gif | both
    domains: list[str] | None = None


class DescribeRequest(BaseModel):
    image_urls: list[str] = Field(min_length=1, max_length=MAX_SELECT)


class StyleProfile(BaseModel):
    descriptors: list[str] = []
    palette: list[str] = []
    avoid: list[str] = []


class RefineRequest(BaseModel):
    board_id: str
    from_round_id: str
    selected_ids: list[str] = Field(min_length=MIN_SELECT, max_length=MAX_SELECT)
    profile: StyleProfile = StyleProfile()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _round_payload(round_id: str) -> dict:
    rnd = db.get_round(round_id)
    return {
        "id": rnd["id"],
        "idx": rnd["idx"],
        "query": rnd["query"],
        "parent_round_id": rnd["parent_round_id"],
        "results": rnd["results"],
    }


def _domains(requested: list[str] | None) -> list[str]:
    if not requested:
        return config.SEARCH_DOMAINS
    allowed = [d for d in requested if d in config.SEARCH_DOMAINS]
    return allowed or config.SEARCH_DOMAINS


def _exa_http_error(exc: exa_client.ExaError) -> HTTPException:
    return HTTPException(status_code=exc.status, detail=str(exc))


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------

@app.get("/api/config")
def get_config():
    return {
        "domains": config.SEARCH_DOMAINS,
        "min_select": MIN_SELECT,
        "max_select": MAX_SELECT,
        "exa_configured": bool(config.EXA_API_KEY),
        "anthropic_configured": bool(config.ANTHROPIC_API_KEY),
    }


@app.post("/api/search")
async def search(req: SearchRequest):
    domains = _domains(req.domains)
    try:
        raw = await exa_client.search(req.vibes, config.OVERFETCH_COUNT, domains)
    except exa_client.ExaError as exc:
        raise _exa_http_error(exc)

    resolved = await images.resolve_images(raw, req.media_type)
    results = images.dedupe(resolved, seen=set())[: config.MAX_RESULTS_PER_ROUND]

    board_id = db.create_board(req.vibes, req.media_type)
    round_id = db.create_round(board_id, idx=1, query=req.vibes, results=results)

    return {"board_id": board_id, "round": _round_payload(round_id)}


@app.post("/api/describe")
async def describe(req: DescribeRequest):
    try:
        return await claude_client.describe_images(req.image_urls)
    except claude_client.DescribeError as exc:
        raise HTTPException(status_code=exc.status, detail=str(exc))


@app.post("/api/refine")
async def refine(req: RefineRequest):
    board = db.get_board(req.board_id)
    if not board:
        raise HTTPException(404, "Board not found.")
    from_round = db.get_round(req.from_round_id)
    if not from_round or from_round["board_id"] != req.board_id:
        raise HTTPException(404, "Round not found.")

    by_id = {r["id"]: r for r in from_round["results"]}
    selected = [by_id[i] for i in req.selected_ids if i in by_id]
    if len(selected) < MIN_SELECT:
        raise HTTPException(400, f"Select at least {MIN_SELECT} results from this round.")

    db.add_selections(req.board_id, req.from_round_id, selected)
    db.update_style_profile(req.board_id, req.profile.model_dump())

    enriched_query = board["vibes"]
    if req.profile.descriptors:
        enriched_query += ", " + ", ".join(req.profile.descriptors)

    domains = config.SEARCH_DOMAINS
    seen = db.seen_urls_for_board(req.board_id)

    try:
        similar = await exa_client.find_similar_many(
            [s["url"] for s in selected], config.FIND_SIMILAR_PER_SELECTION, domains
        )
        fresh = await exa_client.search(enriched_query, config.OVERFETCH_COUNT, domains)
    except exa_client.ExaError as exc:
        raise _exa_http_error(exc)

    # findSimilar results lead — they carry the image-reference signal.
    merged, raw_seen = [], set()
    for r in similar + fresh:
        if r["url"] in raw_seen or r["url"] in seen:
            continue
        raw_seen.add(r["url"])
        merged.append(r)

    resolved = await images.resolve_images(merged, board["media_type"])
    results = images.dedupe(resolved, seen)[: config.MAX_RESULTS_PER_ROUND]

    round_id = db.create_round(
        req.board_id,
        idx=from_round["idx"] + 1,
        query=enriched_query,
        results=results,
        parent_round_id=req.from_round_id,
    )
    return {"board_id": req.board_id, "round": _round_payload(round_id)}


@app.get("/api/board/{board_id}")
def get_board(board_id: str):
    board = db.get_board(board_id)
    if not board:
        raise HTTPException(404, "Board not found.")
    import json as _json

    return {
        "id": board["id"],
        "vibes": board["vibes"],
        "media_type": board["media_type"],
        "style_profile": _json.loads(board["style_profile"]),
        "rounds": [
            {
                "id": r["id"],
                "idx": r["idx"],
                "query": r["query"],
                "parent_round_id": r["parent_round_id"],
                "results": r["results"],
            }
            for r in db.get_rounds_for_board(board_id)
        ],
        "selections": [
            {"round_id": s["round_id"], "result": s["result"]}
            for s in db.get_selections_for_board(board_id)
        ],
    }


@app.get("/api/board/{board_id}/export.json")
def export_json(board_id: str):
    board = get_board(board_id)
    payload = {
        "vibes": board["vibes"],
        "style_profile": board["style_profile"],
        "images": [
            {
                "image_url": s["result"]["image_url"],
                "page_url": s["result"]["url"],
                "source": s["result"]["source"],
            }
            for s in board["selections"]
        ],
    }
    return JSONResponse(
        payload,
        headers={"Content-Disposition": f'attachment; filename="moodboard-{board_id}.json"'},
    )


@app.get("/api/board/{board_id}/export.png")
async def export_png(board_id: str):
    board = get_board(board_id)
    urls = [s["result"]["image_url"] for s in board["selections"]]
    if not urls:
        raise HTTPException(400, "No selections on this board yet.")
    try:
        png = await export.render_contact_sheet(
            board["vibes"], board["style_profile"].get("descriptors", []), urls
        )
    except ValueError as exc:
        raise HTTPException(502, str(exc))
    return Response(
        content=png,
        media_type="image/png",
        headers={"Content-Disposition": f'attachment; filename="moodboard-{board_id}.png"'},
    )


@app.get("/api/img")
async def img_proxy(url: str = Query(...)):
    try:
        body, content_type = await proxy.fetch_image(url)
    except proxy.ProxyError as exc:
        raise HTTPException(status_code=exc.status, detail=str(exc))
    return Response(
        content=body,
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=86400"},
    )


# ---------------------------------------------------------------------------
# Serve the built frontend (production) — `npm run build` in frontend/ first.
# ---------------------------------------------------------------------------

_DIST = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend", "dist")

if os.path.isdir(_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(_DIST, "assets")), name="assets")

    @app.get("/{path:path}")
    def spa(path: str):
        file_path = os.path.join(_DIST, path)
        if path and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(_DIST, "index.html"))
