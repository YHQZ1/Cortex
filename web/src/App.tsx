import { useEffect, useMemo, useState } from "react";

import { AnswerPanel } from "./components/ask/AnswerPanel";
import { AskPanel } from "./components/ask/AskPanel";
import { AppShell } from "./components/layout/AppShell";
import { RepositoryPanel } from "./components/repositories/RepositoryPanel";
import { SetupStrip } from "./components/setup/SetupStrip";
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
      repositoryCount={repositories.repositories.length}
      repositories={repositories.repositories}
      selectedRepository={repositories.repository}
      onSelectRepository={repositories.selectRepository}
    >
      <SetupStrip
        loading={setupLoading}
        setupStatus={setupStatus}
        onRefresh={() => void refreshSetupStatus()}
      />

      {error && (
        <div className="border-b border-red-200 bg-red-50 px-5 py-3 text-sm font-medium text-red-800">
          {error}
        </div>
      )}

      <div className="grid flex-1 gap-4 p-4 xl:grid-cols-[360px_minmax(0,1fr)_360px]">
        <aside className="space-y-4">
          <RepositoryPanel
            action={repositories.action}
            job={repositories.job}
            manualMode={repositories.manualMode}
            manualRepository={repositories.manualRepository}
            owner={repositories.owner}
            ownerRepositories={repositories.ownerRepositories}
            owners={repositories.owners}
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
            onSelectOwner={repositories.selectOwner}
            onSelectRepository={(sourceRef) => {
              repositories.selectRepository(sourceRef);
              setPreview(null);
            }}
          />
        </aside>

        <section className="min-w-0 space-y-4">
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

        <aside>
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
