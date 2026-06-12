async function request(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (body.detail) detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* non-JSON error body */
    }
    const err = new Error(detail);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

export const api = {
  config: () => request("/api/config"),

  search: ({ vibes, mediaType, searchMode, contentType, domains }) =>
    request("/api/search", {
      method: "POST",
      body: JSON.stringify({
        vibes,
        media_type: mediaType,
        search_mode: searchMode,
        content_type: contentType,
        domains,
      }),
    }),

  describe: (imageUrls) =>
    request("/api/describe", {
      method: "POST",
      body: JSON.stringify({ image_urls: imageUrls }),
    }),

  refine: ({ boardId, fromRoundId, selectedIds, profile }) =>
    request("/api/refine", {
      method: "POST",
      body: JSON.stringify({
        board_id: boardId,
        from_round_id: fromRoundId,
        selected_ids: selectedIds,
        profile,
      }),
    }),

  board: (boardId) => request(`/api/board/${boardId}`),
};

export const proxied = (url) => `/api/img?url=${encodeURIComponent(url)}`;
