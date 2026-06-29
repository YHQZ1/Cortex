import { useState } from "react";

import { AskMode, AskResponse, AskSource, streamAskCortex } from "../lib/api";
import { usePersistentState } from "./usePersistentState";

export type RecentQuestion = {
  id: string;
  question: string;
  repository: string;
  mode: AskMode;
  askedAt: string;
};

export function useAsk(onError: (message: string) => void) {
  const [question, setQuestion] = usePersistentState(
    "cortex.question",
    "How does this repository work?",
  );
  const [mode, setMode] = usePersistentState<AskMode>("cortex.askMode", "repository");
  const [limit, setLimit] = usePersistentState("cortex.limit", 3);
  const [answer, setAnswer] = usePersistentState<AskResponse | null>("cortex.latestAnswer", null);
  const [recentQuestions, setRecentQuestions] = usePersistentState<RecentQuestion[]>(
    "cortex.recentQuestions",
    [],
  );
  const [asking, setAsking] = useState(false);

  async function ask(repository: string) {
    const nextQuestion = question.trim();
    if (!nextQuestion) {
      return;
    }

    setAnswer({ question: nextQuestion, answer: "", sources: [] });
    setAsking(true);

    try {
      await streamAskCortex({
        question: nextQuestion,
        repository: repository.trim(),
        limit,
        mode,
        onSources: (sources: AskSource[]) => {
          setAnswer((current) => ({
            question: current?.question ?? nextQuestion,
            answer: current?.answer ?? "",
            sources,
          }));
        },
        onToken: (token: string) => {
          setAnswer((current) => ({
            question: current?.question ?? nextQuestion,
            answer: `${current?.answer ?? ""}${token}`,
            sources: current?.sources ?? [],
          }));
        },
      });
      rememberQuestion(nextQuestion, repository);
    } catch (caught) {
      onError(toErrorMessage(caught));
    } finally {
      setAsking(false);
    }
  }

  function rememberQuestion(nextQuestion: string, repository: string) {
    const entry: RecentQuestion = {
      id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
      question: nextQuestion,
      repository,
      mode,
      askedAt: new Date().toISOString(),
    };

    setRecentQuestions((current) => [
      entry,
      ...current
        .filter(
          (item) =>
            item.question.toLowerCase() !== nextQuestion.toLowerCase() ||
            item.repository !== repository ||
            item.mode !== mode,
        )
        .slice(0, 7),
    ]);
  }

  function restoreQuestion(item: RecentQuestion) {
    setQuestion(item.question);
    setMode(item.mode);
  }

  function clearAnswer() {
    setAnswer(null);
  }

  return {
    answer,
    ask,
    asking,
    clearAnswer,
    limit,
    mode,
    question,
    recentQuestions,
    restoreQuestion,
    setAnswer,
    setLimit,
    setMode,
    setQuestion,
  };
}

function toErrorMessage(error: unknown) {
  return error instanceof Error ? error.message : "Something went wrong.";
}
