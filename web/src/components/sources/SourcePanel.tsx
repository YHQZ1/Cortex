import { Loader2, X } from "lucide-react";

import { AskMode, AskSource, ChunkPreview } from "../../lib/api";

type SourcePanelProps = {
  mode: AskMode;
  preview: ChunkPreview | null;
  previewLoading: boolean;
  sources: AskSource[];
  onClosePreview: () => void;
  onOpenPreview: (chunkId: string) => void;
};

const MAX_SCORE_REFERENCE = 1.6;

export function SourcePanel({
  mode,
  preview,
  previewLoading,
  sources,
  onClosePreview,
  onOpenPreview,
}: SourcePanelProps) {
  const maxScore = Math.max(MAX_SCORE_REFERENCE, ...sources.map((source) => source.score));

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="px-4 py-3.5">
        <span className="text-xs font-semibold uppercase tracking-wide text-ink-soft">Sources</span>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto">
        {sources.length > 0 ? (
          <ul>
            {sources.map((source) => (
              <li key={source.chunk_id}>
                <button
                  className="block w-full border-t border-line-soft px-4 py-3 text-left transition first:border-t-0 hover:bg-line-soft"
                  onClick={() => onOpenPreview(source.chunk_id)}
                  type="button"
                >
                  <div className="truncate font-mono text-xs text-ink">
                    {source.path}
                    <span className="font-medium text-ink-soft">
                      :{source.start_line}-{source.end_line}
                    </span>
                  </div>
                  <div className="mt-1.5 flex items-center gap-2">
                    <RelevanceBar maxScore={maxScore} score={source.score} />
                    <span className="font-mono text-[11px] font-medium text-ink-soft">
                      {source.language ?? "text"}
                    </span>
                  </div>
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p className="px-4 py-2 text-xs font-medium leading-5 text-ink-soft">
            {mode === "repository" ? "No sources retrieved yet." : "General mode does not use sources."}
          </p>
        )}
      </div>

      {(preview || previewLoading) && (
        <div className="max-h-[50%] min-h-0 shrink-0 overflow-y-auto border-t border-line bg-ink">
          <div className="flex items-center justify-between gap-3 border-b border-white/10 px-4 py-2.5">
            <span className="truncate font-mono text-xs text-paper/70">
              {preview ? `${preview.path}:${preview.start_line}-${preview.end_line}` : "loading…"}
            </span>
            <button
              className="shrink-0 text-paper/50 transition hover:text-paper"
              onClick={onClosePreview}
              type="button"
            >
              <X size={14} />
            </button>
          </div>

          {previewLoading ? (
            <div className="flex min-h-24 items-center justify-center text-sm text-paper/50">
              <Loader2 className="mr-2 animate-spin" size={15} />
              loading source
            </div>
          ) : (
            preview && <CodeBlock content={preview.content} startLine={preview.start_line} />
          )}
        </div>
      )}
    </div>
  );
}

function RelevanceBar({ maxScore, score }: { maxScore: number; score: number }) {
  const ratio = Math.max(0, Math.min(1, score / maxScore));
  const filledTicks = Math.max(1, Math.round(ratio * 5));

  return (
    <div className="flex items-center gap-1.5" title={`relevance score ${score.toFixed(3)}`}>
      <div className="flex gap-px">
        {Array.from({ length: 5 }, (_, index) => (
          <span
            className={`h-2.5 w-1 ${index < filledTicks ? "bg-signal" : "bg-line"}`}
            key={index}
          />
        ))}
      </div>
      <span className="font-mono text-[11px] font-medium text-ink-soft">{score.toFixed(2)}</span>
    </div>
  );
}

function CodeBlock({ content, startLine }: { content: string; startLine: number }) {
  const lines = content.split("\n");

  return (
    <pre className="overflow-x-auto p-0 font-mono text-xs leading-5">
      <code>
        {lines.map((line, index) => (
          <div className="flex" key={index}>
            <span className="w-10 shrink-0 select-none px-2 text-right text-paper/30">
              {startLine + index}
            </span>
            <span className="flex-1 whitespace-pre pr-4 text-paper/90">{line || " "}</span>
          </div>
        ))}
      </code>
    </pre>
  );
}
