import { ReactNode } from "react";

import { SetupStatus } from "../../lib/api";
import { SetupStrip } from "../setup/SetupStrip";

type AppShellProps = {
  children: ReactNode;
  selectedRepository: string;
  setupLoading: boolean;
  setupStatus: SetupStatus | null;
  onRefreshSetup: () => void;
};

export function AppShell({
  children,
  selectedRepository,
  setupLoading,
  setupStatus,
  onRefreshSetup,
}: AppShellProps) {
  return (
    <div className="flex h-screen overflow-hidden bg-paper text-ink">
      <div className="flex min-w-0 flex-1 flex-col">
      <header className="flex h-14 shrink-0 items-center justify-between border-b border-line px-5">
        <div className="flex items-center gap-3">
          <span className="font-mono text-sm font-semibold tracking-tight">cortex</span>
          <span className="hidden text-ink-faint sm:inline">/</span>
          <span className="hidden truncate text-sm text-ink-soft sm:inline">
            {selectedRepository || "no repository selected"}
          </span>
        </div>

        <SetupStrip loading={setupLoading} onRefresh={onRefreshSetup} setupStatus={setupStatus} />
      </header>

      <main className="min-h-0 flex-1 overflow-hidden">{children}</main>
      </div>
    </div>
  );
}
