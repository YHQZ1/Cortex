import { RefreshCw } from "lucide-react";

import { SetupStatus } from "../../lib/api";

type SetupStripProps = {
  loading: boolean;
  onRefresh: () => void;
  setupStatus: SetupStatus | null;
};

const CHECK_LABELS: Array<[string, string]> = [
  ["api", "api"],
  ["postgres", "pg"],
  ["redis", "redis"],
  ["qdrant", "qdrant"],
  ["ollama", "ollama"],
  ["embedding_model", "embed"],
  ["llm_model", "llm"],
];

export function SetupStrip({ loading, onRefresh, setupStatus }: SetupStripProps) {
  const ready = setupStatus?.status === "ready";
  const failing = CHECK_LABELS.filter(([key]) => setupStatus?.checks?.[key]?.ok === false);

  return (
    <div className="flex items-center gap-3">
      <button
        className="group flex items-center gap-2 text-xs text-ink-soft transition hover:text-ink"
        onClick={onRefresh}
        title="Refresh setup status"
        type="button"
      >
        <span
          className={`size-1.5 rounded-full ${
            !setupStatus ? "bg-ink-faint" : ready ? "bg-good" : "bg-bad"
          }`}
        />
        <span className="font-mono tracking-tight">
          {!setupStatus ? "checking" : ready ? "ready" : `${failing.length} down`}
        </span>
        <RefreshCw
          className={`size-3 text-ink-faint transition group-hover:text-ink-soft ${loading ? "animate-spin" : ""}`}
        />
      </button>

      {failing.length > 0 && (
        <div className="hidden items-center gap-1.5 md:flex">
          {failing.map(([key, label]) => (
            <span
              className="rounded border border-bad/30 bg-bad-soft px-1.5 py-0.5 font-mono text-[11px] text-bad"
              key={key}
              title={setupStatus?.checks?.[key]?.error ?? undefined}
            >
              {label}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
