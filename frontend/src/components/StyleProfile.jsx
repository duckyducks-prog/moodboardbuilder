function Chip({ text, onRemove, tone = "default" }) {
  const tones = {
    default: "border-zinc-700 bg-zinc-900 text-zinc-300",
    avoid: "border-red-900/60 bg-red-950/40 text-red-300/80",
  };
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs ${tones[tone]}`}>
      {text}
      {onRemove && (
        <button
          onClick={onRemove}
          className="text-zinc-500 transition hover:text-zinc-200"
          title="Remove from style profile"
        >
          ×
        </button>
      )}
    </span>
  );
}

export default function StyleProfile({ profile, onRemoveDescriptor, onRemoveAvoid, readOnly = false }) {
  const { descriptors = [], palette = [], avoid = [] } = profile;
  if (!descriptors.length && !palette.length && !avoid.length) return null;

  return (
    <div className="mb-5 rounded-xl border border-zinc-900 bg-zinc-950/60 p-3">
      <div className="mb-2 text-[10px] uppercase tracking-widest text-zinc-600">Style profile</div>
      <div className="flex flex-wrap items-center gap-1.5">
        {descriptors.map((d, i) => (
          <Chip key={`d-${d}`} text={d} onRemove={readOnly ? null : () => onRemoveDescriptor(i)} />
        ))}
        {palette.map((c) => {
          const isHex = /^#[0-9a-f]{3,8}$/i.test(c.trim());
          return (
            <span key={`p-${c}`} className="inline-flex items-center gap-1.5 rounded-full border border-zinc-800 px-2.5 py-1 text-xs text-zinc-400">
              {isHex && <span className="h-3 w-3 rounded-full border border-zinc-700" style={{ background: c }} />}
              {c}
            </span>
          );
        })}
        {avoid.map((a, i) => (
          <Chip key={`a-${a}`} text={`not: ${a}`} tone="avoid" onRemove={readOnly ? null : () => onRemoveAvoid(i)} />
        ))}
      </div>
    </div>
  );
}
