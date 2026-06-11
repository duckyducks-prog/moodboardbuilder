export default function RoundRail({ rounds, activeIdx, onJump }) {
  return (
    <div className="flex flex-col items-center gap-1 pt-1">
      {rounds.map((round, i) => (
        <div key={round.id} className="flex flex-col items-center">
          {i > 0 && <div className="h-4 w-px bg-zinc-800" />}
          <button
            onClick={() => onJump(i)}
            title={round.query}
            className={`flex h-9 w-9 items-center justify-center rounded-full border text-sm transition ${
              i === activeIdx
                ? "border-orange-400 bg-orange-400/10 text-orange-300"
                : "border-zinc-800 text-zinc-500 hover:border-zinc-600 hover:text-zinc-300"
            }`}
          >
            {round.idx}
          </button>
        </div>
      ))}
    </div>
  );
}
