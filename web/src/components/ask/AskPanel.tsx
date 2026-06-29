import { Loader2, MessageSquareText, SlidersHorizontal } from "lucide-react";

import { AskMode } from "../../lib/api";
import { RecentQuestion } from "../../hooks/useAsk";

type AskPanelProps = {
  asking: boolean;
  limit: number;
  mode: AskMode;
  question: string;
  recentQuestions: RecentQuestion[];
  repository: string;
  onAsk: () => void;
  onLimitChange: (limit: number) => void;
  onModeChange: (mode: AskMode) => void;
  onQuestionChange: (question: string) => void;
  onRestoreQuestion: (question: RecentQuestion) => void;
};

export function AskPanel({
  asking,
  limit,
  mode,
  question,
  recentQuestions,
  repository,
  onAsk,
  onLimitChange,
  onModeChange,
  onQuestionChange,
  onRestoreQuestion,
}: AskPanelProps) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white">
      <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3">
        <div className="flex items-center gap-2">
          <MessageSquareText size={18} />
          <h3 className="text-sm font-semibold">Ask</h3>
        </div>
        <ModeToggle mode={mode} onModeChange={onModeChange} />
      </div>

      <div className="space-y-4 p-4">
        <textarea
          className="min-h-32 w-full resize-y rounded-md border border-slate-200 bg-slate-50 p-3 text-sm leading-6 outline-none transition focus:border-teal-600 focus:bg-white"
          onChange={(event) => onQuestionChange(event.target.value)}
          placeholder={mode === "repository" ? `Ask about ${repository}` : "Ask anything"}
          value={question}
        />

        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div className="flex min-w-0 items-center gap-3 rounded-md border border-slate-200 bg-slate-50 px-3 py-2">
            <SlidersHorizontal size={16} className="shrink-0 text-slate-500" />
            <input
              className="w-40 accent-teal-700"
              max="8"
              min="1"
              onChange={(event) => onLimitChange(Number(event.target.value))}
              type="range"
              value={limit}
            />
            <span className="w-5 text-center text-sm font-semibold text-slate-900">{limit}</span>
          </div>

          <button
            className="inline-flex h-10 min-w-28 items-center justify-center gap-2 rounded-md bg-teal-700 px-4 text-sm font-semibold text-white transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={asking || !question.trim() || (mode === "repository" && !repository.trim())}
            onClick={onAsk}
            type="button"
          >
            {asking && <Loader2 className="animate-spin" size={16} />}
            Ask
          </button>
        </div>

        {recentQuestions.length > 0 && (
          <div className="border-t border-slate-100 pt-3">
            <div className="mb-2 text-xs font-semibold uppercase text-slate-500">Recent</div>
            <div className="flex gap-2 overflow-x-auto pb-1">
              {recentQuestions.slice(0, 5).map((item) => (
                <button
                  className="max-w-64 shrink-0 truncate rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 transition hover:border-teal-500 hover:text-slate-950"
                  key={item.id}
                  onClick={() => onRestoreQuestion(item)}
                  title={item.question}
                  type="button"
                >
                  {item.question}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

function ModeToggle({
  mode,
  onModeChange,
}: {
  mode: AskMode;
  onModeChange: (mode: AskMode) => void;
}) {
  return (
    <div className="inline-grid grid-cols-2 rounded-md border border-slate-200 bg-slate-100 p-1">
      {(["repository", "general"] as const).map((item) => (
        <button
          className={`h-8 rounded px-3 text-xs font-semibold capitalize transition ${
            mode === item ? "bg-white text-slate-950 shadow-sm" : "text-slate-500 hover:text-slate-900"
          }`}
          key={item}
          onClick={() => onModeChange(item)}
          type="button"
        >
          {item}
        </button>
      ))}
    </div>
  );
}
