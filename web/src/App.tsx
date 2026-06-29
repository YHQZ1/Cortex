import { useEffect, useMemo, useState } from "react";

import { AnswerPanel } from "./components/ask/AnswerPanel";
import { AskPanel } from "./components/ask/AskPanel";
import { AppShell } from "./components/layout/AppShell";
import { RepositoryPanel } from "./components/repositories/RepositoryPanel";
import { SourcePanel } from "./components/sources/SourcePanel";
import { useAsk } from "./hooks/useAsk";
import { usePersistentState } from "./hooks/usePersistentState";
import { useRepositories } from "./hooks/useRepositories";
import { ChunkPreview, SetupStatus, getChunkPreview, getSetupStatus } from "./lib/api";

function App() {
  const [error, setError] = useState<string | null>(null);
  const [setupStatus, setSetupStatus] = useState<SetupStatus | null>(null);
  const [setupLoading, setSetupLoading] = useState(false);
  const [preview, setPreview] = usePersistentState<ChunkPreview | null>("cortex.preview", null);
  const [previewLoading, setPreviewLoading] = useState(false);

  const repositories = useRepositories(setError);
  const ask = useAsk(setError);

  useEffect(() => {
    void refreshSetupStatus();
  }, []);

  const sources = useMemo(() => ask.answer?.sources ?? [], [ask.answer?.sources]);

  async function refreshSetupStatus() {
    setSetupLoading(true);
    try {
      setSetupStatus(await getSetupStatus());
    } catch (caught) {
      setError(toErrorMessage(caught));
    } finally {
      setSetupLoading(false);
    }
  }

  async function handleAsk() {
    setError(null);
    setPreview(null);
    await ask.ask(repositories.repository);
  }

  async function handlePreview(chunkId: string) {
    setError(null);
    setPreviewLoading(true);
    try {
      setPreview(await getChunkPreview(chunkId));
    } catch (caught) {
      setError(toErrorMessage(caught));
    } finally {
      setPreviewLoading(false);
    }
  }

  return (
    <AppShell
      onRefreshSetup={() => void refreshSetupStatus()}
      selectedRepository={repositories.repository}
      setupLoading={setupLoading}
      setupStatus={setupStatus}
    >
      {error && (
        <div className="border-b border-bad/30 bg-bad-soft px-5 py-2.5 text-sm text-bad">{error}</div>
      )}

      <div className="grid h-full min-h-0 lg:grid-cols-[240px_minmax(0,1fr)_320px]">
        <aside className="min-h-0 overflow-hidden border-b border-line lg:border-b-0 lg:border-r">
          <RepositoryPanel
            action={repositories.action}
            job={repositories.job}
            manualMode={repositories.manualMode}
            manualRepository={repositories.manualRepository}
            repositories={repositories.repositories}
            repository={repositories.repository}
            selectedRepository={repositories.selectedRepository}
            onDelete={() => {
              setError(null);
              ask.clearAnswer();
              setPreview(null);
              void repositories.deleteSelectedRepository();
            }}
            onIngest={() => {
              setError(null);
              ask.clearAnswer();
              setPreview(null);
              void repositories.ingestRepository();
            }}
            onManualModeChange={repositories.setManualMode}
            onManualRepositoryChange={repositories.updateManualRepository}
            onReindex={() => {
              setError(null);
              ask.clearAnswer();
              setPreview(null);
              void repositories.reindexSelectedRepository();
            }}
            onSelectRepository={(sourceRef) => {
              repositories.selectRepository(sourceRef);
              setPreview(null);
            }}
          />
        </aside>

        <section className="flex min-h-0 min-w-0 flex-col gap-4 overflow-hidden border-b border-line p-5 lg:border-b-0">
          <AskPanel
            asking={ask.asking}
            limit={ask.limit}
            mode={ask.mode}
            question={ask.question}
            recentQuestions={ask.recentQuestions}
            repository={repositories.repository}
            onAsk={() => void handleAsk()}
            onLimitChange={ask.setLimit}
            onModeChange={ask.setMode}
            onQuestionChange={ask.setQuestion}
            onRestoreQuestion={ask.restoreQuestion}
            onStop={ask.stop}
          />
          <AnswerPanel
            answer={ask.answer}
            asking={ask.asking}
            mode={ask.mode}
            onClear={() => {
              ask.clearAnswer();
              setPreview(null);
            }}
          />
        </section>

        <aside className="min-h-0 overflow-hidden border-line lg:border-l">
          <SourcePanel
            mode={ask.mode}
            preview={preview}
            previewLoading={previewLoading}
            sources={sources}
            onClosePreview={() => setPreview(null)}
            onOpenPreview={(chunkId) => void handlePreview(chunkId)}
          />
        </aside>
      </div>
    </AppShell>
  );
}

function toErrorMessage(error: unknown) {
  return error instanceof Error ? error.message : "Something went wrong.";
}

export default App;
