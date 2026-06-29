import { Loader2, X } from "lucide-react";

import { AskMode, AskResponse } from "../../lib/api";

type AnswerPanelProps = {
  answer: AskResponse | null;
  asking: boolean;
  mode: AskMode;
  onClear: () => void;
};

export function AnswerPanel({ answer, asking, mode, onClear }: AnswerPanelProps) {
  if (!answer) {
    return (
      <div className="flex min-h-0 flex-1 items-center justify-center overflow-hidden border border-dashed border-line text-sm font-medium text-ink-soft">
        {mode === "repository" ? "Repository answers will appear here." : "General answers will appear here."}
      </div>
    );
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col overflow-hidden border border-line bg-surface">
      <div className="flex items-center justify-between gap-3 border-b border-line-soft px-4 py-2.5">
        <p className="truncate text-xs font-medium text-ink-soft">{answer.question}</p>
        <button
          className="shrink-0 text-ink-faint transition hover:text-ink"
          onClick={onClear}
          title="Clear answer"
          type="button"
        >
          <X size={14} />
        </button>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto p-5">
        {asking && !answer.answer && (
          <div className="flex items-center gap-2 text-sm font-medium text-ink-soft">
            <Loader2 className="animate-spin" size={15} />
            thinking…
          </div>
        )}
        {answer.answer && (
          <p className="max-w-[72ch] whitespace-pre-wrap text-[15px] leading-7 text-ink">
            {answer.answer}
            {asking && <span className="ml-0.5 inline-block h-4 w-[2px] -translate-y-0.5 animate-pulse bg-signal" />}
          </p>
        )}
      </div>
    </div>
  );
}
