import { Loader2, Plus, RefreshCw, Trash2 } from "lucide-react";

import { IngestionJob, RepositorySummary } from "../../lib/api";

type RepositoryPanelProps = {
  action: "ingest" | "reindex" | "delete" | null;
  job: IngestionJob | null;
  manualMode: boolean;
  manualRepository: string;
  repositories: RepositorySummary[];
  repository: string;
  selectedRepository: RepositorySummary | null;
  onDelete: () => void;
  onIngest: () => void;
  onManualModeChange: (enabled: boolean) => void;
  onManualRepositoryChange: (value: string) => void;
  onReindex: () => void;
  onSelectRepository: (sourceRef: string) => void;
};

export function RepositoryPanel({
  action,
  job,
  manualMode,
  manualRepository,
  repositories,
  repository,
  selectedRepository,
  onDelete,
  onIngest,
  onManualModeChange,
  onManualRepositoryChange,
  onReindex,
  onSelectRepository,
}: RepositoryPanelProps) {
  const jobIsWorking = job?.status === "pending" || job?.status === "running";
  const progress = job ? getJobProgress(job) : null;

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex items-center justify-between px-4 py-3.5">
        <span className="text-xs font-semibold uppercase tracking-wide text-ink-soft">
          Repositories
        </span>
        <button
          className="flex items-center gap-1 bg-signal-soft px-2 py-1 font-mono text-xs font-semibold text-signal transition hover:bg-signal-soft/70"
          onClick={() => onManualModeChange(!manualMode)}
          type="button"
        >
          <Plus size={12} />
          new
        </button>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto">
        {manualMode && (
          <div className="px-4 pb-3">
            <input
              autoFocus
              className="h-10 w-full border border-line bg-surface px-3 font-mono text-xs font-semibold text-ink caret-signal placeholder:text-ink-soft focus:border-signal"
              onChange={(event) => onManualRepositoryChange(event.target.value)}
              placeholder="owner/repo or github url"
              value={manualRepository}
            />
            {manualRepository.trim() && repository !== manualRepository.trim() && (
              <div className="mt-1.5 font-mono text-[11px] font-medium text-ink-soft">
                will resolve to <span className="font-semibold text-signal">{repository}</span>
              </div>
            )}
          </div>
        )}

        {repositories.length > 0 ? (
          <ul>
            {repositories.map((item) => {
              const selected = item.source_ref === repository;
              return (
                <li key={item.source_ref}>
                  <button
                    className={`block w-full border-l-2 px-4 py-2.5 text-left transition ${
                      selected
                        ? "border-signal bg-signal-soft/40"
                        : "border-transparent hover:bg-line-soft"
                    }`}
                    onClick={() => onSelectRepository(item.source_ref)}
                    type="button"
                  >
                    <div className="truncate text-sm font-medium text-ink">{item.name}</div>
                    <div className="mt-0.5 truncate font-mono text-[11px] font-medium text-ink-soft">
                      {item.source_ref} · {item.file_count}f · {item.chunk_count}c
                    </div>
                  </button>
                </li>
              );
            })}
          </ul>
        ) : (
          <p className="px-4 py-2 text-xs font-medium leading-5 text-ink-soft">
            Nothing indexed yet. Enter a repository above and ingest it.
          </p>
        )}
      </div>

      <div className="border-t border-line p-4">
        <button
          className="flex h-10 w-full items-center justify-center gap-2 border border-line bg-line-soft text-sm font-bold text-ink shadow-sm transition hover:border-signal/40 hover:bg-signal-soft disabled:cursor-not-allowed disabled:border-line disabled:bg-line-soft disabled:text-ink-soft disabled:shadow-none"
          disabled={action !== null || !repository.trim() || jobIsWorking}
          onClick={onIngest}
          type="button"
        >
          {action === "ingest" || jobIsWorking ? <Loader2 className="animate-spin" size={15} /> : null}
          {selectedRepository ? "Ingest latest" : "Ingest repository"}
        </button>

        {selectedRepository && (
          <div className="mt-2 grid grid-cols-2 gap-2">
            <button
              className="flex h-8 items-center justify-center gap-1.5 border border-line bg-surface text-xs font-bold text-ink transition hover:border-ink-soft hover:bg-line-soft disabled:cursor-not-allowed disabled:text-ink-faint disabled:opacity-70"
              disabled={action !== null || jobIsWorking}
              onClick={onReindex}
              type="button"
            >
              {action === "reindex" ? <Loader2 className="animate-spin" size={12} /> : <RefreshCw size={12} />}
              Reindex
            </button>
            <button
              className="flex h-8 items-center justify-center gap-1.5 border border-line bg-surface text-xs font-bold text-ink transition hover:border-bad hover:bg-bad-soft hover:text-bad disabled:cursor-not-allowed disabled:text-ink-faint disabled:opacity-70"
              disabled={action !== null || jobIsWorking}
              onClick={onDelete}
              type="button"
            >
              {action === "delete" ? <Loader2 className="animate-spin" size={12} /> : <Trash2 size={12} />}
              Delete
            </button>
          </div>
        )}

        {job && (
          <div className="mt-3 text-xs leading-5">
            <div
              className={`mb-1 font-mono font-medium ${
                job.status === "succeeded"
                  ? "text-good"
                  : job.status === "failed"
                    ? "text-bad"
                    : "text-ink-soft"
              }`}
            >
              {job.status}
            </div>
            {progress && (
              <div className="mb-2">
                <div className="mb-1 flex items-center justify-between gap-2 font-mono text-[11px] font-semibold text-ink-soft">
                  <span className="truncate">{progress.label}</span>
                  <span>{progress.percent}%</span>
                </div>
                <div className="h-1.5 overflow-hidden bg-line-soft">
                  <div
                    className={`h-full transition-all duration-300 ${
                      job.status === "failed" ? "bg-bad" : "bg-signal"
                    }`}
                    style={{ width: `${progress.percent}%` }}
                  />
                </div>
                <div className="mt-1 font-mono text-[11px] font-medium text-ink-soft">
                  {job.progress_current}/{job.progress_total}
                </div>
              </div>
            )}
            <p className="font-medium text-ink-soft">{job.message}</p>
          </div>
        )}
      </div>
    </div>
  );
}

function getJobProgress(job: IngestionJob) {
  if (job.status === "succeeded") {
    return { label: "complete", percent: 100 };
  }
  if (job.status === "failed") {
    const percent = calculatePercent(job.progress_current, job.progress_total);
    return { label: job.progress_stage ?? "failed", percent };
  }

  return {
    label: job.progress_stage ?? job.status,
    percent: calculatePercent(job.progress_current, job.progress_total),
  };
}

function calculatePercent(current: number, total: number) {
  if (total <= 0) {
    return 0;
  }
  return Math.max(0, Math.min(100, Math.round((current / total) * 100)));
}
