import { useState } from "react";
import { proxied } from "../api";
import StyleProfile from "./StyleProfile";

export default function BoardView({ board, readOnly = false }) {
  const [copied, setCopied] = useState(false);
  const selections = board.selections || [];

  const copyShareLink = async () => {
    const url = `${window.location.origin}/board/${board.id}`;
    try {
      await navigator.clipboard.writeText(url);
    } catch {
      window.prompt("Copy this link:", url);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="text-[10px] uppercase tracking-widest text-zinc-600">Moodboard</div>
          <h2 className="max-w-2xl text-xl text-zinc-200">{board.vibes}</h2>
        </div>
        <div className="flex gap-2">
          <a
            href={`/api/board/${board.id}/export.png`}
            className="rounded-lg border border-zinc-800 px-3 py-1.5 text-sm text-zinc-300 transition hover:border-zinc-600"
          >
            Export PNG
          </a>
          <a
            href={`/api/board/${board.id}/export.json`}
            className="rounded-lg border border-zinc-800 px-3 py-1.5 text-sm text-zinc-300 transition hover:border-zinc-600"
          >
            Export JSON
          </a>
          {!readOnly && (
            <button
              onClick={copyShareLink}
              className="rounded-lg border border-zinc-800 px-3 py-1.5 text-sm text-zinc-300 transition hover:border-zinc-600"
            >
              {copied ? "Copied ✓" : "Share link"}
            </button>
          )}
        </div>
      </div>

      <StyleProfile profile={board.style_profile || {}} readOnly />

      {selections.length === 0 ? (
        <div className="py-24 text-center text-zinc-600">
          Nothing selected yet — refine at least one round to build the board.
        </div>
      ) : (
        <div className="masonry">
          {selections.map((s, i) => (
            <a
              key={`${s.result.id}-${i}`}
              href={s.result.url}
              target="_blank"
              rel="noreferrer"
              className="group relative mb-3 block overflow-hidden rounded-xl"
              style={{ breakInside: "avoid" }}
            >
              <img src={proxied(s.result.image_url)} alt={s.result.title || ""} loading="lazy" className="w-full" />
              <span className="absolute bottom-2 left-2 rounded bg-black/60 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-zinc-300 opacity-0 transition group-hover:opacity-100">
                {s.result.source.replace(/\.(com|net)$/, "")}
              </span>
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
