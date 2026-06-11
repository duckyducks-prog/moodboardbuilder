import { useState } from "react";
import { proxied } from "../api";

function Card({ result, selected, onToggle, hoverAnimate, readOnly }) {
  const [hovered, setHovered] = useState(false);
  const [failed, setFailed] = useState(false);

  if (failed) return null;

  // GIF perf option: show the still thumbnail and only animate on hover.
  const showStill = result.media === "gif" && hoverAnimate && result.still_url && !hovered;
  const src = proxied(showStill ? result.still_url : result.image_url);

  return (
    <div
      className={`group relative mb-3 cursor-pointer overflow-hidden rounded-xl transition ${
        selected ? "ring-2 ring-orange-400 ring-offset-2 ring-offset-[#0a0a0c]" : ""
      }`}
      style={{ breakInside: "avoid" }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onClick={() => !readOnly && onToggle(result.id)}
    >
      <img
        src={src}
        alt={result.title || "result"}
        loading="lazy"
        onError={() => setFailed(true)}
        className={`w-full transition ${selected ? "opacity-100" : "opacity-90 group-hover:opacity-100"}`}
      />

      {selected && (
        <div className="absolute right-2 top-2 flex h-6 w-6 items-center justify-center rounded-full bg-orange-400 text-sm font-bold text-zinc-950">
          ✓
        </div>
      )}

      <div className="pointer-events-none absolute inset-x-0 bottom-0 flex items-end justify-between bg-gradient-to-t from-black/80 to-transparent p-2 opacity-0 transition group-hover:opacity-100">
        <span className="rounded bg-black/60 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-zinc-300">
          {result.source.replace(/\.(com|net)$/, "")}
          {result.media === "gif" && " · gif"}
        </span>
        <a
          href={result.url}
          target="_blank"
          rel="noreferrer"
          onClick={(e) => e.stopPropagation()}
          className="pointer-events-auto rounded bg-black/60 px-1.5 py-0.5 text-[10px] text-zinc-300 hover:text-white"
        >
          open ↗
        </a>
      </div>
    </div>
  );
}

export default function ResultsGrid({ results, selectedIds, onToggle, hoverAnimate, readOnly = false }) {
  if (!results.length) {
    return (
      <div className="py-24 text-center text-zinc-600">
        No usable results came back for this round. Try rewording the vibes or widening the sources.
      </div>
    );
  }
  return (
    <div className="masonry">
      {results.map((r) => (
        <Card
          key={r.id}
          result={r}
          selected={selectedIds.has(r.id)}
          onToggle={onToggle}
          hoverAnimate={hoverAnimate}
          readOnly={readOnly}
        />
      ))}
    </div>
  );
}
