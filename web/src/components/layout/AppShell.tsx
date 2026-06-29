import { Brain, Github, SearchCode } from "lucide-react";
import { ReactNode } from "react";

import { RepositorySummary } from "../../lib/api";

type AppShellProps = {
  children: ReactNode;
  repositoryCount: number;
  repositories: RepositorySummary[];
  selectedRepository: string;
  onSelectRepository: (sourceRef: string) => void;
};

export function AppShell({
  children,
  repositoryCount,
  repositories,
  selectedRepository,
  onSelectRepository,
}: AppShellProps) {
  return (
    <main className="min-h-screen bg-[#f7f7f4] text-slate-900">
      <div className="grid min-h-screen lg:grid-cols-[260px_1fr]">
        <aside className="hidden border-r border-slate-200 bg-[#101820] text-white lg:flex lg:flex-col">
          <div className="border-b border-white/10 px-5 py-5">
            <div className="flex items-center gap-3">
              <div className="flex size-10 items-center justify-center rounded-lg bg-teal-400 text-[#101820]">
                <Brain size={21} />
              </div>
              <div>
                <h1 className="text-lg font-semibold">Cortex</h1>
                <p className="text-xs text-slate-300">{repositoryCount} indexed repositories</p>
              </div>
            </div>
          </div>

          <div className="flex-1 overflow-auto px-3 py-4">
            <div className="mb-2 flex items-center gap-2 px-2 text-xs font-semibold uppercase text-slate-400">
              <Github size={14} />
              Library
            </div>
            <div className="space-y-1">
              {repositories.length > 0 ? (
                repositories.map((repository) => (
                  <button
                    className={`w-full rounded-md px-3 py-2 text-left transition ${
                      repository.source_ref === selectedRepository
                        ? "bg-white text-slate-950"
                        : "text-slate-300 hover:bg-white/10 hover:text-white"
                    }`}
                    key={repository.source_ref}
                    onClick={() => onSelectRepository(repository.source_ref)}
                    type="button"
                  >
                    <div className="truncate text-sm font-semibold">{repository.name}</div>
                    <div className="mt-0.5 truncate text-xs opacity-70">{repository.source_ref}</div>
                  </button>
                ))
              ) : (
                <div className="rounded-md border border-white/10 px-3 py-3 text-sm text-slate-300">
                  No indexed repositories
                </div>
              )}
            </div>
          </div>

          <div className="border-t border-white/10 px-5 py-4 text-xs text-slate-400">
            FastAPI · Qdrant · Ollama
          </div>
        </aside>

        <section className="flex min-w-0 flex-col">
          <header className="border-b border-slate-200 bg-white px-5 py-4">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <div className="mb-1 flex items-center gap-2 text-xs font-semibold uppercase text-slate-500 lg:hidden">
                  <Brain size={14} />
                  Cortex
                </div>
                <h2 className="text-xl font-semibold tracking-normal text-slate-950">
                  Repository assistant
                </h2>
                <p className="mt-1 text-sm text-slate-500">
                  {selectedRepository || "Select or ingest a repository"}
                </p>
              </div>
              <div className="inline-flex w-fit items-center gap-2 rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-medium text-slate-600">
                <SearchCode size={16} />
                Local RAG
              </div>
            </div>
          </header>

          {children}
        </section>
      </div>
    </main>
  );
}
