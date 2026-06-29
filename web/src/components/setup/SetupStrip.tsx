import { CheckCircle2, Info, RefreshCw, TriangleAlert } from "lucide-react";

import { SetupStatus } from "../../lib/api";

type SetupStripProps = {
  loading: boolean;
  onRefresh: () => void;
  setupStatus: SetupStatus | null;
};

export function SetupStrip({ loading, onRefresh, setupStatus }: SetupStripProps) {
  const checks = [
    ["API", setupStatus?.checks.api],
    ["Postgres", setupStatus?.checks.postgres],
    ["Redis", setupStatus?.checks.redis],
    ["Qdrant", setupStatus?.checks.qdrant],
    ["Ollama", setupStatus?.checks.ollama],
    ["Embeddings", setupStatus?.checks.embedding_model],
    ["LLM", setupStatus?.checks.llm_model],
  ] as const;
  const ready = setupStatus?.status === "ready";

  return (
    <section
      className={`flex flex-col gap-3 border-b px-5 py-3 lg:flex-row lg:items-center lg:justify-between ${
        ready
          ? "border-emerald-200 bg-emerald-50 text-emerald-900"
          : "border-amber-200 bg-amber-50 text-amber-950"
      }`}
    >
      <div className="flex items-center gap-2 text-sm font-semibold">
        {ready ? <CheckCircle2 size={17} /> : <TriangleAlert size={17} />}
        {ready ? "Cortex is ready" : "Setup needs attention"}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {checks.map(([label, check]) => (
          <span
            className={`inline-flex h-7 items-center gap-1 rounded-full border bg-white px-2.5 text-xs font-medium ${
              check?.ok
                ? "border-emerald-200 text-emerald-700"
                : "border-amber-200 text-amber-800"
            }`}
            key={label}
            title={check?.error ?? undefined}
          >
            {check?.ok ? <CheckCircle2 size={12} /> : <Info size={12} />}
            {label}
          </span>
        ))}
        <button
          className="inline-flex h-7 items-center gap-1 rounded-full border border-slate-200 bg-white px-2.5 text-xs font-semibold text-slate-600 transition hover:border-slate-300 hover:text-slate-900 disabled:opacity-60"
          disabled={loading}
          onClick={onRefresh}
          type="button"
        >
          <RefreshCw className={loading ? "animate-spin" : ""} size={12} />
          Refresh
        </button>
      </div>
    </section>
  );
}
