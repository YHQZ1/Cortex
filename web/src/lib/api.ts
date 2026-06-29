const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export type IngestionJob = {
  id: string;
  status: "pending" | "running" | "succeeded" | "failed";
  source_type: string;
  source_ref: string;
  message: string;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
  updated_at: string;
};

export type AskSource = {
  chunk_id: string;
  repository: string;
  path: string;
  language: string | null;
  start_line: number;
  end_line: number;
  score: number;
};

export type AskResponse = {
  question: string;
  answer: string;
  sources: AskSource[];
};

export type ChunkPreview = {
  chunk_id: string;
  repository: string;
  path: string;
  language: string | null;
  start_line: number;
  end_line: number;
  content: string;
};

export type RepositorySummary = {
  source_type: string;
  source_ref: string;
  name: string;
  default_branch: string | null;
  last_indexed_at: string | null;
  file_count: number;
  chunk_count: number;
};

export type SetupCheck = {
  ok: boolean;
  name?: string;
  url?: string;
  error?: string | null;
};

export type SetupStatus = {
  status: "ready" | "needs_setup";
  checks: Record<string, SetupCheck>;
  commands: {
    embedding_model: string;
    llm_model: string;
  };
};

export async function getSetupStatus(): Promise<SetupStatus> {
  return request<SetupStatus>("/setup");
}

export async function listRepositories(): Promise<RepositorySummary[]> {
  return request<RepositorySummary[]>("/repositories");
}

export async function createIngestion(sourceRef: string): Promise<IngestionJob> {
  return request<IngestionJob>("/ingestions", {
    method: "POST",
    body: JSON.stringify({
      source_type: "github",
      source_ref: sourceRef,
    }),
  });
}

export async function reindexRepository(sourceRef: string): Promise<IngestionJob> {
  return request<IngestionJob>(`/repositories/${encodeURIComponent(sourceRef)}/reindex`, {
    method: "POST",
  });
}

export async function deleteRepository(sourceRef: string): Promise<void> {
  await request<void>(`/repositories/${encodeURIComponent(sourceRef)}`, {
    method: "DELETE",
  });
}

export async function getIngestion(jobId: string): Promise<IngestionJob> {
  return request<IngestionJob>(`/ingestions/${jobId}`);
}

export async function getChunkPreview(chunkId: string): Promise<ChunkPreview> {
  return request<ChunkPreview>(`/chunks/${chunkId}`);
}

export async function askCortex(params: {
  question: string;
  repository?: string;
  limit: number;
}): Promise<AskResponse> {
  return request<AskResponse>("/ask", {
    method: "POST",
    body: JSON.stringify({
      question: params.question,
      repository: params.repository || null,
      limit: params.limit,
    }),
  });
}

export async function streamAskCortex(params: {
  question: string;
  repository?: string;
  limit: number;
  onSources: (sources: AskSource[]) => void;
  onToken: (token: string) => void;
}): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/ask/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      question: params.question,
      repository: params.repository || null,
      limit: params.limit,
    }),
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with status ${response.status}`);
  }

  if (!response.body) {
    throw new Error("Streaming response was empty.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      if (!line.trim()) {
        continue;
      }
      handleStreamEvent(JSON.parse(line), params);
    }
  }

  if (buffer.trim()) {
    handleStreamEvent(JSON.parse(buffer), params);
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init.headers,
    },
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with status ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

function handleStreamEvent(
  event: { type: string; sources?: AskSource[]; content?: string },
  params: {
    onSources: (sources: AskSource[]) => void;
    onToken: (token: string) => void;
  },
) {
  if (event.type === "sources") {
    params.onSources(event.sources ?? []);
  }
  if (event.type === "token" && event.content) {
    params.onToken(event.content);
  }
}
