const HEIGHTS = [180, 260, 220, 320, 200, 280, 240, 190, 300, 230, 210, 270];

export default function Skeletons() {
  return (
    <div className="masonry">
      {HEIGHTS.map((h, i) => (
        <div
          key={i}
          className="mb-3 animate-pulse rounded-xl bg-zinc-900"
          style={{ height: h, breakInside: "avoid" }}
        />
      ))}
    </div>
  );
}
