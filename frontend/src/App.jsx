import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";
import VibeInput from "./components/VibeInput";
import ResultsGrid from "./components/ResultsGrid";
import RoundRail from "./components/RoundRail";
import StyleProfile from "./components/StyleProfile";
import BoardView from "./components/BoardView";
import Skeletons from "./components/Skeletons";
import Toast from "./components/Toast";

const DEFAULT_DOMAINS = [
  "dribbble.com",
  "behance.net",
  "pinterest.com",
  "eyecannndy.com",
  "giphy.com",
  "film-grab.com",
  "shotdeck.com",
  "shot.cafe",
  "frameset.app",
  "movie-screencaps.com",
  "evanerichards.com",
  "vimeo.com",
];
const MAX_DESCRIBE_IMAGES = 8; // style analysis samples at most this many selections

function mergeUnique(existing, incoming) {
  const seen = new Set(existing.map((s) => s.toLowerCase().trim()));
  const merged = [...existing];
  for (const item of incoming || []) {
    const key = item.toLowerCase().trim();
    if (key && !seen.has(key)) {
      seen.add(key);
      merged.push(item);
    }
  }
  return merged;
}

export default function App() {
  // Read-only share route: /board/:id
  const shareMatch = window.location.pathname.match(/^\/board\/([a-z0-9]+)$/i);

  const [cfg, setCfg] = useState(null);
  const [boardId, setBoardId] = useState(shareMatch ? shareMatch[1] : null);
  const [rounds, setRounds] = useState([]); // {id, idx, query, results, selectedIds:Set}
  const [activeIdx, setActiveIdx] = useState(0);
  const [profile, setProfile] = useState({ descriptors: [], palette: [], avoid: [] });
  const [loading, setLoading] = useState(null); // 'search' | 'refine' | 'board'
  const [view, setView] = useState(shareMatch ? "share" : "input");
  const [boardData, setBoardData] = useState(null);
  const [hoverAnimate, setHoverAnimate] = useState(false);
  const [toast, setToast] = useState(null);
  const toastTimer = useRef(null);

  const showToast = useCallback((msg) => {
    clearTimeout(toastTimer.current);
    setToast(msg);
    toastTimer.current = setTimeout(() => setToast(null), 5000);
  }, []);

  useEffect(() => {
    api.config().then(setCfg).catch(() => setCfg({ domains: DEFAULT_DOMAINS }));
  }, []);

  useEffect(() => {
    if (view === "share" && boardId) {
      api
        .board(boardId)
        .then(setBoardData)
        .catch((e) => showToast(e.message));
    }
  }, [view, boardId, showToast]);

  const activeRound = rounds[activeIdx];

  const handleSearch = async ({ vibes, mediaType, searchMode, contentType, domains }) => {
    setLoading("search");
    try {
      const data = await api.search({ vibes, mediaType, searchMode, contentType, domains });
      setBoardId(data.board_id);
      setRounds([{ ...data.round, selectedIds: new Set() }]);
      setActiveIdx(0);
      setProfile({ descriptors: [], palette: [], avoid: [] });
      setView("rounds");
    } catch (e) {
      showToast(e.message);
    } finally {
      setLoading(null);
    }
  };

  const toggleSelect = (id) => {
    setRounds((prev) =>
      prev.map((round, i) => {
        if (i !== activeIdx) return round;
        const next = new Set(round.selectedIds);
        if (next.has(id)) next.delete(id);
        else next.add(id);
        return { ...round, selectedIds: next };
      })
    );
  };

  const handleRefine = async () => {
    const round = rounds[activeIdx];
    const selectedIds = [...round.selectedIds];
    setLoading("refine");

    let nextProfile = profile;
    if (selectedIds.length > 0) {
      try {
        const byId = new Map(round.results.map((r) => [r.id, r]));
        const imageUrls = selectedIds.slice(0, MAX_DESCRIBE_IMAGES).map((id) => byId.get(id).image_url);
        const dna = await api.describe(imageUrls);
        nextProfile = {
          descriptors: mergeUnique(profile.descriptors, dna.descriptors),
          palette: mergeUnique(profile.palette, dna.palette),
          avoid: mergeUnique(profile.avoid, dna.avoid),
        };
        setProfile(nextProfile);
      } catch (e) {
        // Style description is an enhancement — refine still works without it.
        showToast(`Style analysis skipped: ${e.message}`);
      }
    }

    try {
      const data = await api.refine({
        boardId,
        fromRoundId: round.id,
        selectedIds,
        profile: nextProfile,
      });
      setRounds((prev) => [...prev, { ...data.round, selectedIds: new Set() }]);
      setActiveIdx(rounds.length);
    } catch (e) {
      showToast(e.message);
    } finally {
      setLoading(null);
    }
  };

  const openBoard = async () => {
    setLoading("board");
    try {
      setBoardData(await api.board(boardId));
      setView("board");
    } catch (e) {
      showToast(e.message);
    } finally {
      setLoading(null);
    }
  };

  // ----- read-only share view -----
  if (view === "share") {
    return (
      <div className="mx-auto max-w-6xl px-6 py-10">
        {boardData ? <BoardView board={boardData} readOnly /> : <Skeletons />}
        <Toast toast={toast} />
      </div>
    );
  }

  // ----- vibe input -----
  if (view === "input") {
    return (
      <>
        <VibeInput domains={cfg?.domains || DEFAULT_DOMAINS} onSearch={handleSearch} busy={loading === "search"} />
        {loading === "search" && (
          <div className="mx-auto max-w-6xl px-6 pb-10">
            <Skeletons />
          </div>
        )}
        <Toast toast={toast} />
      </>
    );
  }

  // ----- board view -----
  if (view === "board") {
    return (
      <div className="mx-auto max-w-6xl px-6 py-10">
        <button onClick={() => setView("rounds")} className="mb-6 text-sm text-zinc-500 transition hover:text-zinc-300">
          ← Back to rounds
        </button>
        {boardData && <BoardView board={boardData} />}
        <Toast toast={toast} />
      </div>
    );
  }

  // ----- rounds view -----
  const selectedCount = activeRound ? activeRound.selectedIds.size : 0;
  const canRefine = !loading && !!activeRound;

  return (
    <div className="mx-auto flex max-w-7xl gap-6 px-6 py-8">
      <aside className="sticky top-8 h-fit w-12 shrink-0">
        <RoundRail rounds={rounds} activeIdx={activeIdx} onJump={setActiveIdx} />
      </aside>

      <main className="min-w-0 flex-1">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div className="min-w-0">
            <button
              onClick={() => setView("input")}
              className="text-[10px] uppercase tracking-widest text-zinc-600 transition hover:text-zinc-400"
            >
              ← New search
            </button>
            <h2 className="truncate text-lg text-zinc-200" title={activeRound?.query}>
              Round {activeRound?.idx} <span className="text-zinc-600">· {activeRound?.query}</span>
            </h2>
          </div>
          <div className="flex items-center gap-3">
            <label className="flex cursor-pointer items-center gap-1.5 text-xs text-zinc-500">
              <input
                type="checkbox"
                checked={hoverAnimate}
                onChange={(e) => setHoverAnimate(e.target.checked)}
                className="accent-orange-400"
              />
              GIFs on hover only
            </label>
            <button
              onClick={openBoard}
              className="rounded-lg border border-zinc-800 px-3 py-1.5 text-sm text-zinc-300 transition hover:border-zinc-600"
            >
              View board
            </button>
            <button
              onClick={handleRefine}
              disabled={!canRefine}
              title={
                selectedCount > 0
                  ? "Refine using your selections"
                  : "Nothing close? Get a fresh batch for the same vibes"
              }
              className="rounded-lg bg-orange-400 px-4 py-1.5 text-sm font-medium text-zinc-950 transition hover:bg-orange-300 disabled:cursor-not-allowed disabled:opacity-30"
            >
              {loading === "refine"
                ? selectedCount > 0
                  ? "Refining…"
                  : "Refreshing…"
                : selectedCount > 0
                  ? `Refine with ${selectedCount}`
                  : "Refresh results"}
            </button>
          </div>
        </div>

        <StyleProfile
          profile={profile}
          onRemoveDescriptor={(i) =>
            setProfile((p) => ({ ...p, descriptors: p.descriptors.filter((_, j) => j !== i) }))
          }
          onRemoveAvoid={(i) => setProfile((p) => ({ ...p, avoid: p.avoid.filter((_, j) => j !== i) }))}
        />

        {loading === "refine" ? (
          <Skeletons />
        ) : (
          activeRound && (
            <ResultsGrid
              results={activeRound.results}
              selectedIds={activeRound.selectedIds}
              onToggle={toggleSelect}
              hoverAnimate={hoverAnimate}
            />
          )
        )}
      </main>

      <Toast toast={toast} />
    </div>
  );
}
