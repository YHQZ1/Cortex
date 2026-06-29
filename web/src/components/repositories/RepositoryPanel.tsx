import {
  CheckCircle2,
  Clock3,
  Github,
  Loader2,
  Plus,
  RefreshCw,
  Trash2,
} from "lucide-react";

import { IngestionJob, RepositorySummary } from "../../lib/api";

type RepositoryPanelProps = {
  action: "ingest" | "reindex" | "delete" | null;
  job: IngestionJob | null;
  manualMode: boolean;
  manualRepository: string;
  owner: string;
  ownerRepositories: RepositorySummary[];
  owners: string[];
  repository: string;
  selectedRepository: RepositorySummary | null;
  onDelete: () => void;
  onIngest: () => void;
  onManualModeChange: (enabled: boolean) => void;
  onManualRepositoryChange: (value: string) => void;
  onReindex: () => void;
  onSelectOwner: (owner: string) => void;
  onSelectRepository: (sourceRef: string) => void;
};

export function RepositoryPanel({
  action,
  job,
  manualMode,
  manualRepository,
  owner,
  ownerRepositories,
  owners,
  repository,
  selectedRepository,
  onDelete,
  onIngest,
  onManualModeChange,
  onManualRepositoryChange,
  onReindex,
  onSelectOwner,
  onSelectRepository,
}: RepositoryPanelProps) {
  const jobIsWorking = job?.status === "pending" || job?.status === "running";

  return (
    <section className="rounded-lg border border-slate-200 bg-white">
      <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3">
        <div className="flex items-center gap-2">
          <Github size={18} />
          <h3 className="text-sm font-semibold">Repository</h3>
        </div>
        {job && <StatusBadge status={job.status} />}
      </div>

      <div className="space-y-4 p-4">
        <div>
          <div className="mb-2 flex items-center justify-between">
            <label className="text-xs font-semibold uppercase text-slate-500">GitHub source</label>
            <button
              className="inline-flex items-center gap-1 text-xs font-semibold text-teal-700 transition hover:text-teal-900"
              onClick={() => onManualModeChange(!manualMode)}
              type="button"
            >
              <Plus size={13} />
              {manualMode ? "Use library" : "New repo"}
            </button>
          </div>

          {manualMode ? (
            <input
              className="h-11 w-full rounded-md border border-slate-200 bg-slate-50 px-3 text-sm outline-none transition focus:border-teal-600 focus:bg-white"
              onChange={(event) => onManualRepositoryChange(event.target.value)}
              placeholder="owner/repo or https://github.com/owner/repo"
              value={manualRepository}
            />
          ) : (
            <div className="grid grid-cols-2 gap-2">
              <select
                className="h-11 min-w-0 rounded-md border border-slate-200 bg-slate-50 px-3 text-sm outline-none transition focus:border-teal-600 focus:bg-white disabled:opacity-60"
                disabled={owners.length === 0}
                onChange={(event) => onSelectOwner(event.target.value)}
                value={owner}
              >
                {owners.length === 0 ? (
                  <option value={owner}>owner</option>
                ) : (
                  owners.map((item) => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))
                )}
              </select>

              <select
                className="h-11 min-w-0 rounded-md border border-slate-200 bg-slate-50 px-3 text-sm outline-none transition focus:border-teal-600 focus:bg-white disabled:opacity-60"
                disabled={ownerRepositories.length === 0}
                onChange={(event) => onSelectRepository(event.target.value)}
                value={repository}
              >
                {ownerRepositories.length === 0 ? (
                  <option value={repository}>repo</option>
                ) : (
                  ownerRepositories.map((item) => (
                    <option key={item.source_ref} value={item.source_ref}>
                      {item.name}
                    </option>
                  ))
                )}
              </select>
            </div>
          )}
          {manualMode && manualRepository.trim() && repository !== manualRepository.trim() && (
            <div className="mt-2 rounded-md border border-teal-100 bg-teal-50 px-3 py-2 text-xs font-medium text-teal-800">
              Will index {repository}
            </div>
          )}
        </div>

        {selectedRepository && (
          <div className="rounded-md border border-slate-200 bg-slate-50 p-3">
            <div className="grid grid-cols-3 gap-2 text-center">
              <Metric label="files" value={selectedRepository.file_count} />
              <Metric label="chunks" value={selectedRepository.chunk_count} />
              <Metric label="branch" value={selectedRepository.default_branch ?? "main"} />
            </div>
            <div className="mt-3 grid grid-cols-2 gap-2">
              <button
                className="inline-flex h-9 items-center justify-center gap-2 rounded-md border border-slate-200 bg-white px-3 text-xs font-semibold text-slate-700 transition hover:border-teal-500 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={action !== null || jobIsWorking}
                onClick={onReindex}
                type="button"
              >
                {action === "reindex" ? <Loader2 className="animate-spin" size={14} /> : <RefreshCw size={14} />}
                Reindex
              </button>
              <button
                className="inline-flex h-9 items-center justify-center gap-2 rounded-md border border-red-200 bg-white px-3 text-xs font-semibold text-red-700 transition hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={action !== null || jobIsWorking}
                onClick={onDelete}
                type="button"
              >
                {action === "delete" ? <Loader2 className="animate-spin" size={14} /> : <Trash2 size={14} />}
                Delete
              </button>
            </div>
          </div>
        )}

        <button
          className="inline-flex h-11 w-full items-center justify-center gap-2 rounded-md bg-slate-950 px-4 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={action !== null || !repository.trim() || jobIsWorking}
          onClick={onIngest}
          type="button"
        >
          {action === "ingest" || jobIsWorking ? (
            <Loader2 className="animate-spin" size={17} />
          ) : (
            <Github size={17} />
          )}
          {selectedRepository ? "Ingest latest" : "Ingest repository"}
        </button>

        {job && (
          <div className={`rounded-md border px-3 py-3 text-sm ${jobClassName(job.status)}`}>
            <div className="mb-2 flex items-center gap-2 font-semibold">
              {job.status === "succeeded" ? <CheckCircle2 size={16} /> : <Clock3 size={16} />}
              {job.status}
            </div>
            <p className="leading-5">{job.message}</p>
          </div>
        )}
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: number | string }) {
  return (
    <div>
      <div className="truncate text-base font-semibold text-slate-950">{value}</div>
      <div className="text-xs text-slate-500">{label}</div>
    </div>
  );
}

function StatusBadge({ status }: { status: IngestionJob["status"] }) {
  const className =
    status === "succeeded"
      ? "border-emerald-200 bg-emerald-50 text-emerald-700"
      : status === "failed"
        ? "border-red-200 bg-red-50 text-red-700"
        : "border-blue-200 bg-blue-50 text-blue-700";

  return <span className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${className}`}>{status}</span>;
}

function jobClassName(status: IngestionJob["status"]) {
  if (status === "succeeded") return "border-emerald-200 bg-emerald-50 text-emerald-800";
  if (status === "failed") return "border-red-200 bg-red-50 text-red-800";
  return "border-blue-200 bg-blue-50 text-blue-800";
}
