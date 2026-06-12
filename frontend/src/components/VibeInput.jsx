import { useState } from "react";

const MEDIA_OPTIONS = [
  { value: "both", label: "All media" },
  { value: "static", label: "Static" },
  { value: "gif", label: "Moving" }, // GIFs + looping videos
];

const MODE_OPTIONS = [
  { value: "vibes", label: "Vibes" },
  { value: "technical", label: "Technical" },
];

const CONTENT_OPTIONS = [
  { value: "both", label: "Any" },
  { value: "motion", label: "Motion design" },
  { value: "live", label: "Live action" },
];

function ToggleGroup({ options, value, onChange }) {
  return (
    <div className="flex rounded-lg border border-zinc-800 p-0.5">
      {options.map((opt) => (
        <button
          key={opt.value}
          type="button"
          onClick={() => onChange(opt.value)}
          className={`rounded-md px-3 py-1 text-sm transition ${
            value === opt.value ? "bg-zinc-800 text-zinc-100" : "text-zinc-500 hover:text-zinc-300"
          }`}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}

export default function VibeInput({ domains, onSearch, busy }) {
  const [vibes, setVibes] = useState("");
  const [mediaType, setMediaType] = useState("both");
  const [searchMode, setSearchMode] = useState("vibes");
  const [contentType, setContentType] = useState("both");
  const [activeDomains, setActiveDomains] = useState(new Set(domains));

  const toggleDomain = (d) => {
    setActiveDomains((prev) => {
      const next = new Set(prev);
      if (next.has(d)) {
        if (next.size > 1) next.delete(d);
      } else {
        next.add(d);
      }
      return next;
    });
  };

  const submit = (e) => {
    e.preventDefault();
    if (vibes.trim().length < 2 || busy) return;
    onSearch({ vibes: vibes.trim(), mediaType, searchMode, contentType, domains: [...activeDomains] });
  };

  return (
    <form onSubmit={submit} className="mx-auto flex min-h-[80vh] w-full max-w-3xl flex-col items-center justify-center px-6">
      <h1 className="mb-2 text-4xl font-semibold tracking-tight text-zinc-100">Moodboard Builder</h1>
      <p className="mb-10 text-zinc-500">Type the vibes. Pick what's close. Refine until it's right.</p>

      <textarea
        value={vibes}
        onChange={(e) => setVibes(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) submit(e);
        }}
        placeholder={
          searchMode === "technical"
            ? '"glassmorphism animation", "kinetic typography", "anamorphic lens flare"'
            : '"sun-bleached 16mm nostalgia, coastal Brazil, slow zooms, grain"'
        }
        rows={4}
        autoFocus
        className="w-full resize-none rounded-2xl border border-zinc-800 bg-zinc-950 p-5 text-lg text-zinc-100 placeholder-zinc-600 outline-none transition focus:border-zinc-600"
      />

      <div className="mt-6 flex w-full flex-wrap items-center gap-2">
        <ToggleGroup options={MODE_OPTIONS} value={searchMode} onChange={setSearchMode} />
        <ToggleGroup options={CONTENT_OPTIONS} value={contentType} onChange={setContentType} />
        <ToggleGroup options={MEDIA_OPTIONS} value={mediaType} onChange={setMediaType} />
        <div className="mx-2 h-5 w-px bg-zinc-800" />
        {domains.map((d) => (
          <button
            key={d}
            type="button"
            onClick={() => toggleDomain(d)}
            className={`rounded-full border px-3 py-1 text-xs transition ${
              activeDomains.has(d)
                ? "border-zinc-700 bg-zinc-900 text-zinc-300"
                : "border-zinc-900 text-zinc-600 hover:text-zinc-400"
            }`}
          >
            {d.replace(/\.(com|net)$/, "")}
          </button>
        ))}
      </div>

      <button
        type="submit"
        disabled={vibes.trim().length < 2 || busy}
        className="mt-10 rounded-xl bg-zinc-100 px-8 py-3 font-medium text-zinc-950 transition hover:bg-white disabled:cursor-not-allowed disabled:opacity-30"
      >
        {busy ? "Searching…" : "Search the vibes"}
      </button>
    </form>
  );
}
