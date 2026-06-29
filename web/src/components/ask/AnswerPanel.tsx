import { FileText, Loader2, X } from "lucide-react";

import { AskMode, AskResponse } from "../../lib/api";

type AnswerPanelProps = {
  answer: AskResponse | null;
  asking: boolean;
  mode: AskMode;
  onClear: () => void;
};

export function AnswerPanel({ answer, asking, mode, onClear }: AnswerPanelProps) {
  return (
    <section className="flex min-h-[440px] flex-col rounded-lg border border-slate-200 bg-white">
      <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3">
        <div>
          <h3 className="text-sm font-semibold">Answer</h3>
          {answer && <p className="mt-0.5 max-w-xl truncate text-xs text-slate-500">{answer.question}</p>}
        </div>
        {answer && (
          <button
            className="rounded-md p-1.5 text-slate-500 transition hover:bg-slate-100 hover:text-slate-950"
            onClick={onClear}
            title="Clear answer"
            type="button"
          >
            <X size={16} />
          </button>
        )}
      </div>

      <article className="flex-1 p-5">
        {answer ? (
          <div>
            {asking && (
              <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-teal-50 px-3 py-1 text-xs font-semibold text-teal-700">
                <Loader2 className="animate-spin" size={13} />
                streaming
              </div>
            )}
            {answer.answer ? (
              <p className="whitespace-pre-wrap text-sm leading-7 text-slate-800">{answer.answer}</p>
            ) : (
              <LoadingState />
            )}
          </div>
        ) : (
          <EmptyState mode={mode} />
        )}
      </article>
    </section>
  );
}

function LoadingState() {
  return (
    <div className="flex min-h-72 items-center justify-center text-sm text-slate-500">
      <Loader2 className="mr-2 animate-spin" size={18} />
      Thinking...
    </div>
  );
}

function EmptyState({ mode }: { mode: AskMode }) {
  return (
    <div className="flex min-h-72 flex-col items-center justify-center text-center text-sm leading-6 text-slate-500">
      <FileText className="mb-3 text-slate-300" size={34} />
      {mode === "repository" ? "Repository answers will appear here." : "General answers will appear here."}
    </div>
  );
}
