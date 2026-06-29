import { FileCode2, Loader2, X } from "lucide-react";

import { AskMode, AskSource, ChunkPreview } from "../../lib/api";

type SourcePanelProps = {
  mode: AskMode;
  preview: ChunkPreview | null;
  previewLoading: boolean;
  sources: AskSource[];
  onClosePreview: () => void;
  onOpenPreview: (chunkId: string) => void;
};

export function SourcePanel({
  mode,
  preview,
  previewLoading,
  sources,
  onClosePreview,
  onOpenPreview,
}: SourcePanelProps) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white">
      <div className="border-b border-slate-100 px-4 py-3">
        <h3 className="text-sm font-semibold">Sources</h3>
      </div>

      <div className="space-y-3 p-4">
        {sources.length > 0 ? (
          sources.map((source, index) => (
            <button
              className="w-full rounded-md border border-slate-200 bg-slate-50 p-3 text-left transition hover:border-teal-500 hover:bg-white"
              key={source.chunk_id}
              onClick={() => onOpenPreview(source.chunk_id)}
              type="button"
            >
              <div className="mb-2 flex items-center justify-between gap-2">
                <span className="text-sm font-semibold">Source {index + 1}</span>
                <span className="rounded-full bg-white px-2 py-0.5 text-xs font-medium text-slate-500">
                  {source.score.toFixed(3)}
                </span>
              </div>
              <div className="break-words font-mono text-xs leading-5 text-slate-700">
                {source.path}:{source.start_line}-{source.end_line}
              </div>
              <div className="mt-2 text-xs text-slate-500">
                {source.language ?? "unknown"} · {source.repository}
              </div>
            </button>
          ))
        ) : (
          <div className="rounded-md border border-dashed border-slate-200 p-4 text-sm leading-6 text-slate-500">
            {mode === "repository" ? "No sources selected yet." : "General mode has no sources."}
          </div>
        )}

        {(preview || previewLoading) && (
          <div className="rounded-md border border-slate-200 bg-white">
            <div className="flex items-start justify-between gap-3 border-b border-slate-100 p-3">
              <div className="min-w-0">
                <div className="mb-1 flex items-center gap-2 text-sm font-semibold">
                  <FileCode2 size={15} />
                  Preview
                </div>
                {preview && (
                  <div className="break-words font-mono text-xs leading-5 text-slate-600">
                    {preview.path}:{preview.start_line}-{preview.end_line}
                  </div>
                )}
              </div>
              <button
                className="rounded-md p-1 text-slate-500 transition hover:bg-slate-100 hover:text-slate-950"
                onClick={onClosePreview}
                type="button"
              >
                <X size={16} />
              </button>
            </div>
            {previewLoading ? (
              <div className="flex min-h-32 items-center justify-center p-4 text-sm text-slate-500">
                <Loader2 className="mr-2 animate-spin" size={16} />
                Loading source...
              </div>
            ) : (
              preview && (
                <pre className="max-h-96 overflow-auto whitespace-pre-wrap p-3 font-mono text-xs leading-5 text-slate-800">
                  {preview.content}
                </pre>
              )
            )}
          </div>
        )}
      </div>
    </section>
  );
}
