export default function Toast({ toast }) {
  if (!toast) return null;
  return (
    <div className="fixed bottom-6 left-1/2 z-50 -translate-x-1/2 rounded-lg border border-red-900/60 bg-red-950/90 px-4 py-2.5 text-sm text-red-200 shadow-xl backdrop-blur">
      {toast}
    </div>
  );
}
