import { ArrowUp, Square } from "lucide-react";
import type { KeyboardEvent } from "react";

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
  onStop: () => void;
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
  onStop,
}: AskPanelProps) {
  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
      event.preventDefault();
      onAsk();
    }
  }

  return (
    <div className="border border-line bg-surface">
      <div className="relative">
        <textarea
          className="min-h-28 w-full resize-y bg-transparent p-4 pr-16 text-[15px] font-medium leading-6 text-ink caret-signal placeholder:text-ink-soft"
          onChange={(event) => onQuestionChange(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={mode === "repository" ? `Ask about ${repository || "a repository"}…` : "Ask anything…"}
          value={question}
        />
        <button
          className={`absolute bottom-3 right-3 flex size-10 items-center justify-center border shadow-sm transition ${
            asking
              ? "border-bad bg-bad text-white hover:bg-bad/85"
              : "border-line bg-line-soft text-ink hover:border-signal/40 hover:bg-signal-soft"
          } disabled:cursor-not-allowed disabled:border-line disabled:bg-line-soft disabled:text-ink-soft disabled:shadow-none`}
          disabled={!asking && (!question.trim() || (mode === "repository" && !repository.trim()))}
          onClick={asking ? onStop : onAsk}
          title={asking ? "Stop generating" : "Ask (⌘ + Enter)"}
          type="button"
        >
          {asking ? <Square fill="currentColor" size={14} /> : <ArrowUp size={16} />}
        </button>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-line-soft px-4 py-2.5">
        <div className="flex items-center gap-1 font-mono text-xs font-semibold">
          {(["repository", "general"] as const).map((item) => (
            <button
              className={`px-2 py-1 transition ${
                mode === item ? "bg-signal-soft text-signal" : "text-ink hover:bg-line-soft"
              }`}
              key={item}
              onClick={() => onModeChange(item)}
              type="button"
            >
              {mode === item ? "● " : "○ "}
              {item}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <span className="font-mono text-xs font-semibold text-ink-soft">sources</span>
          <input
            className="w-28 accent-signal"
            max="8"
            min="1"
            onChange={(event) => onLimitChange(Number(event.target.value))}
            type="range"
            value={limit}
          />
          <span className="w-3 font-mono text-xs font-semibold text-ink">{limit}</span>
        </div>
      </div>

      {recentQuestions.length > 0 && (
        <div className="flex gap-1.5 overflow-x-auto border-t border-line-soft px-4 py-2.5">
          {recentQuestions.slice(0, 5).map((item) => (
            <button
              className="shrink-0 truncate border border-line-soft bg-surface px-2.5 py-1 text-xs font-semibold text-ink transition hover:border-signal/40 hover:bg-line-soft"
              key={item.id}
              onClick={() => onRestoreQuestion(item)}
              title={item.question}
              type="button"
            >
              {item.question.length > 48 ? `${item.question.slice(0, 48)}…` : item.question}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
