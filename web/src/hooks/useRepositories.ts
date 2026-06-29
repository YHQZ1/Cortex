import { useEffect, useMemo, useState } from "react";

import {
  IngestionJob,
  RepositorySummary,
  createIngestion,
  deleteRepository,
  getIngestion,
  listRepositories,
  reindexRepository,
} from "../lib/api";
import { normalizeGitHubRepositoryInput } from "../lib/github";
import { usePersistentState } from "./usePersistentState";

const DEFAULT_REPOSITORY = "YHQZ1/ESX";

export function useRepositories(onError: (message: string) => void) {
  const [repository, setRepository] = usePersistentState("cortex.repository", DEFAULT_REPOSITORY);
  const [manualRepository, setManualRepository] = usePersistentState(
    "cortex.manualRepository",
    DEFAULT_REPOSITORY,
  );
  const [manualMode, setManualMode] = usePersistentState("cortex.manualMode", false);
  const [repositories, setRepositories] = useState<RepositorySummary[]>([]);
  const [job, setJob] = usePersistentState<IngestionJob | null>("cortex.latestJob", null);
  const [loading, setLoading] = useState(false);
  const [action, setAction] = useState<"ingest" | "reindex" | "delete" | null>(null);

  const activeJob = job?.status === "pending" || job?.status === "running";

  useEffect(() => {
    void refreshRepositories();
  }, []);

  useEffect(() => {
    if (!job || !activeJob) {
      return;
    }

    const interval = window.setInterval(async () => {
      try {
        const updatedJob = await getIngestion(job.id);
        setJob(updatedJob);
        if (updatedJob.status === "succeeded") {
          await refreshRepositories();
        }
      } catch (caught) {
        onError(toErrorMessage(caught));
      }
    }, 1000);

    return () => window.clearInterval(interval);
  }, [activeJob, job, onError, setJob]);

  const selectedRepository = useMemo(
    () => repositories.find((item) => item.source_ref === repository) ?? null,
    [repositories, repository],
  );

  const owners = useMemo(
    () => Array.from(new Set(repositories.map((item) => item.source_ref.split("/")[0]))).sort(),
    [repositories],
  );

  const owner = repository.split("/")[0] || DEFAULT_REPOSITORY.split("/")[0];

  const ownerRepositories = useMemo(
    () =>
      repositories
        .filter((item) => item.source_ref.startsWith(`${owner}/`))
        .sort((left, right) => left.name.localeCompare(right.name)),
    [owner, repositories],
  );

  async function refreshRepositories() {
    setLoading(true);
    try {
      const indexedRepositories = await listRepositories();
      setRepositories(indexedRepositories);

      const currentExists = indexedRepositories.some((item) => item.source_ref === repository);
      if (!manualMode && indexedRepositories.length > 0 && !currentExists) {
        selectRepository(indexedRepositories[0].source_ref);
      }
    } catch (caught) {
      onError(toErrorMessage(caught));
    } finally {
      setLoading(false);
    }
  }

  function selectRepository(sourceRef: string) {
    setRepository(sourceRef);
    setManualRepository(sourceRef);
  }

  function selectOwner(nextOwner: string) {
    const firstRepo = repositories.find((item) => item.source_ref.startsWith(`${nextOwner}/`));
    if (firstRepo) {
      selectRepository(firstRepo.source_ref);
    }
  }

  async function ingestRepository() {
    const sourceRef = normalizeGitHubRepositoryInput(repository);
    if (!sourceRef) {
      return;
    }

    setRepository(sourceRef);
    setManualRepository(sourceRef);
    setAction("ingest");
    try {
      const nextJob = await createIngestion(sourceRef);
      setJob(nextJob);
      await refreshRepositories();
    } catch (caught) {
      onError(toErrorMessage(caught));
    } finally {
      setAction(null);
    }
  }

  async function reindexSelectedRepository() {
    if (!selectedRepository) {
      return;
    }

    setAction("reindex");
    try {
      setJob(await reindexRepository(selectedRepository.source_ref));
    } catch (caught) {
      onError(toErrorMessage(caught));
    } finally {
      setAction(null);
    }
  }

  async function deleteSelectedRepository() {
    if (!selectedRepository) {
      return;
    }

    const shouldDelete = window.confirm(`Delete indexed repository ${selectedRepository.source_ref}?`);
    if (!shouldDelete) {
      return;
    }

    setAction("delete");
    try {
      await deleteRepository(selectedRepository.source_ref);
      const remainingRepositories = await listRepositories();
      setRepositories(remainingRepositories);
      setJob(null);

      if (remainingRepositories.length > 0) {
        selectRepository(remainingRepositories[0].source_ref);
      } else {
        setManualMode(true);
      }
    } catch (caught) {
      onError(toErrorMessage(caught));
    } finally {
      setAction(null);
    }
  }

  function updateManualRepository(sourceRef: string) {
    setManualRepository(sourceRef);
    setRepository(normalizeGitHubRepositoryInput(sourceRef));
  }

  return {
    action,
    activeJob,
    ingestRepository,
    job,
    loading,
    manualMode,
    manualRepository,
    owner,
    ownerRepositories,
    owners,
    refreshRepositories,
    repositories,
    repository,
    selectedRepository,
    selectOwner,
    selectRepository,
    setManualMode,
    updateManualRepository,
    reindexSelectedRepository,
    deleteSelectedRepository,
  };
}

function toErrorMessage(error: unknown) {
  return error instanceof Error ? error.message : "Something went wrong.";
}
