import { Brain, CheckCircle2, Clock3, Github, Loader2, MessageSquareText, SearchCode } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { AskResponse, IngestionJob, askCortex, createIngestion, getIngestion } from "./lib/api";

const DEFAULT_REPOSITORY = "YHQZ1/ESX";

function App() {
  const [repository, setRepository] = useState(DEFAULT_REPOSITORY);
  const [question, setQuestion] = useState("How does ESX use events and message streaming?");
  const [limit, setLimit] = useState(3);
  const [job, setJob] = useState<IngestionJob | null>(null);
  const [answer, setAnswer] = useState<AskResponse | null>(null);
  const [ingesting, setIngesting] = useState(false);
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const activeJob = job?.status === "pending" || job?.status === "running";

  useEffect(() => {
    if (!job || !activeJob) {
      return;
    }

    const interval = window.setInterval(async () => {
      try {
        setJob(await getIngestion(job.id));
      } catch (caught) {
        setError(toErrorMessage(caught));
      }
    }, 2500);

    return () => window.clearInterval(interval);
  }, [activeJob, job]);

  const jobTone = useMemo(() => {
    if (!job) return "idle";
    if (job.status === "succeeded") return "success";
    if (job.status === "failed") return "danger";
    return "working";
  }, [job]);

  async function handleIngest() {
    setError(null);
    setAnswer(null);
    setIngesting(true);
    try {
      setJob(await createIngestion(repository.trim()));
    } catch (caught) {
      setError(toErrorMessage(caught));
    } finally {
      setIngesting(false);
    }
  }

  async function handleAsk() {
    setError(null);
    setAsking(true);
    try {
      setAnswer(
        await askCortex({
          question: question.trim(),
          repository: repository.trim(),
          limit,
        }),
      );
    } catch (caught) {
      setError(toErrorMessage(caught));
    } finally {
      setAsking(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#f5f2ec] text-[#1f2933]">
      <section className="mx-auto flex min-h-screen w-full max-w-7xl flex-col px-5 py-6 sm:px-8">
        <header className="flex flex-col gap-4 border-b border-[#d8d1c5] pb-5 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-[#c9c0b3] bg-white/70 px-3 py-1 text-xs font-medium text-[#52606d]">
              <Brain size={14} />
              Local RAG console
            </div>
            <h1 className="text-3xl font-semibold tracking-normal text-[#111827] sm:text-4xl">
              Cortex
            </h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-[#52606d]">
              Ingest a GitHub repository, ask questions against indexed code, and inspect the exact
              source chunks behind each answer.
            </p>
          </div>
          <div className="rounded-md border border-[#d8d1c5] bg-white px-3 py-2 text-sm text-[#52606d]">
            FastAPI · Qdrant · Ollama
          </div>
        </header>

        {error && (
          <div className="mt-5 rounded-md border border-[#d94848] bg-[#fff1f1] px-4 py-3 text-sm text-[#9b1c1c]">
            {error}
          </div>
        )}

        <div className="grid flex-1 gap-5 py-5 lg:grid-cols-[360px_1fr]">
          <aside className="space-y-5">
            <section className="rounded-md border border-[#d8d1c5] bg-white p-4">
              <div className="mb-4 flex items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <Github size={18} />
                  <h2 className="text-base font-semibold">Repository</h2>
                </div>
                {job && <StatusBadge status={job.status} />}
              </div>

              <label className="text-xs font-medium uppercase text-[#697586]" htmlFor="repository">
                GitHub source
              </label>
              <input
                id="repository"
                className="mt-2 h-11 w-full rounded-md border border-[#c9c0b3] bg-[#faf9f6] px-3 text-sm outline-none transition focus:border-[#2f6f6d] focus:bg-white"
                value={repository}
                onChange={(event) => setRepository(event.target.value)}
                placeholder="owner/repo"
              />

              <button
                className="mt-4 inline-flex h-11 w-full items-center justify-center gap-2 rounded-md bg-[#1f2933] px-4 text-sm font-semibold text-white transition hover:bg-[#111827] disabled:cursor-not-allowed disabled:opacity-60"
                disabled={ingesting || !repository.trim()}
                onClick={handleIngest}
              >
                {ingesting ? <Loader2 className="animate-spin" size={17} /> : <SearchCode size={17} />}
                Ingest repository
              </button>

              {job && (
                <div className={`mt-4 rounded-md border px-3 py-3 text-sm ${jobClassName(jobTone)}`}>
                  <div className="mb-2 flex items-center gap-2 font-medium">
                    {job.status === "succeeded" ? <CheckCircle2 size={16} /> : <Clock3 size={16} />}
                    {job.status}
                  </div>
                  <p className="leading-5">{job.message}</p>
                </div>
              )}
            </section>

            <section className="rounded-md border border-[#d8d1c5] bg-white p-4">
              <h2 className="mb-3 text-base font-semibold">Retrieval</h2>
              <label className="text-xs font-medium uppercase text-[#697586]" htmlFor="limit">
                Source chunks
              </label>
              <input
                id="limit"
                type="range"
                min="1"
                max="8"
                value={limit}
                onChange={(event) => setLimit(Number(event.target.value))}
                className="mt-3 w-full accent-[#2f6f6d]"
              />
              <div className="mt-2 flex items-center justify-between text-sm text-[#52606d]">
                <span>faster</span>
                <strong className="text-[#1f2933]">{limit}</strong>
                <span>deeper</span>
              </div>
            </section>
          </aside>

          <section className="flex min-h-[620px] flex-col rounded-md border border-[#d8d1c5] bg-white">
            <div className="border-b border-[#e3ded6] p-4">
              <div className="mb-3 flex items-center gap-2">
                <MessageSquareText size={19} />
                <h2 className="text-base font-semibold">Ask Cortex</h2>
              </div>
              <textarea
                className="min-h-28 w-full resize-y rounded-md border border-[#c9c0b3] bg-[#faf9f6] p-3 text-sm leading-6 outline-none transition focus:border-[#2f6f6d] focus:bg-white"
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="Ask a question about the indexed codebase"
              />
              <div className="mt-3 flex justify-end">
                <button
                  className="inline-flex h-10 min-w-28 items-center justify-center gap-2 rounded-md bg-[#2f6f6d] px-4 text-sm font-semibold text-white transition hover:bg-[#255c5a] disabled:cursor-not-allowed disabled:opacity-60"
                  disabled={asking || !question.trim() || !repository.trim()}
                  onClick={handleAsk}
                >
                  {asking && <Loader2 className="animate-spin" size={16} />}
                  Ask
                </button>
              </div>
            </div>

            <div className="grid flex-1 gap-0 lg:grid-cols-[1fr_340px]">
              <article className="min-h-80 border-b border-[#e3ded6] p-5 lg:border-b-0 lg:border-r">
                {asking ? (
                  <div className="flex h-full min-h-80 items-center justify-center text-sm text-[#52606d]">
                    <Loader2 className="mr-2 animate-spin" size={18} />
                    Generating with local Ollama...
                  </div>
                ) : answer ? (
                  <div>
                    <div className="mb-3 text-xs font-medium uppercase text-[#697586]">Answer</div>
                    <p className="whitespace-pre-wrap text-sm leading-7 text-[#1f2933]">
                      {answer.answer}
                    </p>
                  </div>
                ) : (
                  <div className="flex h-full min-h-80 items-center justify-center text-center text-sm leading-6 text-[#697586]">
                    Ask a question after ingesting a repository.
                    <br />
                    The answer will appear here with citations.
                  </div>
                )}
              </article>

              <aside className="p-4">
                <div className="mb-3 text-xs font-medium uppercase text-[#697586]">Sources</div>
                {answer?.sources.length ? (
                  <div className="space-y-3">
                    {answer.sources.map((source, index) => (
                      <div
                        className="rounded-md border border-[#e3ded6] bg-[#faf9f6] p-3 text-sm"
                        key={source.chunk_id}
                      >
                        <div className="mb-2 flex items-center justify-between gap-2">
                          <span className="font-semibold">Source {index + 1}</span>
                          <span className="text-xs text-[#697586]">{source.score.toFixed(3)}</span>
                        </div>
                        <div className="break-words font-mono text-xs leading-5 text-[#334e68]">
                          {source.path}:{source.start_line}-{source.end_line}
                        </div>
                        <div className="mt-2 text-xs text-[#697586]">
                          {source.language ?? "unknown"} · {source.repository}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="rounded-md border border-dashed border-[#d8d1c5] p-4 text-sm leading-6 text-[#697586]">
                    Retrieved source references will appear here.
                  </div>
                )}
              </aside>
            </div>
          </section>
        </div>
      </section>
    </main>
  );
}

function StatusBadge({ status }: { status: IngestionJob["status"] }) {
  const className =
    status === "succeeded"
      ? "bg-[#e7f6ef] text-[#1f7a4d] border-[#b7e2cc]"
      : status === "failed"
        ? "bg-[#fff1f1] text-[#9b1c1c] border-[#f2b8b5]"
        : "bg-[#edf4ff] text-[#1e5fa8] border-[#bed5f4]";

  return (
    <span className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${className}`}>
      {status}
    </span>
  );
}

function jobClassName(tone: "idle" | "success" | "danger" | "working") {
  if (tone === "success") return "border-[#b7e2cc] bg-[#f0fbf6] text-[#1f7a4d]";
  if (tone === "danger") return "border-[#f2b8b5] bg-[#fff1f1] text-[#9b1c1c]";
  if (tone === "working") return "border-[#bed5f4] bg-[#f3f8ff] text-[#1e5fa8]";
  return "border-[#e3ded6] bg-[#faf9f6] text-[#52606d]";
}

function toErrorMessage(error: unknown) {
  return error instanceof Error ? error.message : "Something went wrong.";
}

export default App;
