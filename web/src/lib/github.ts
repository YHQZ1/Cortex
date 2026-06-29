export function normalizeGitHubRepositoryInput(input: string) {
  const trimmed = input.trim();

  if (!trimmed) {
    return "";
  }

  const withoutGitSuffix = trimmed.replace(/\.git$/i, "");
  const sshMatch = withoutGitSuffix.match(/^git@github\.com:([A-Za-z0-9_.-]+)\/([A-Za-z0-9_.-]+)$/i);
  if (sshMatch) {
    return `${sshMatch[1]}/${sshMatch[2]}`;
  }

  const directMatch = withoutGitSuffix.match(/^([A-Za-z0-9_.-]+)\/([A-Za-z0-9_.-]+)$/);

  if (directMatch) {
    return `${directMatch[1]}/${directMatch[2]}`;
  }

  try {
    const url = new URL(
      withoutGitSuffix.startsWith("http") ? withoutGitSuffix : `https://${withoutGitSuffix}`,
    );

    if (url.hostname !== "github.com" && url.hostname !== "www.github.com") {
      return withoutGitSuffix;
    }

    const [owner, repo] = url.pathname.split("/").filter(Boolean);

    if (!owner || !repo) {
      return withoutGitSuffix;
    }

    return `${owner}/${repo}`;
  } catch {
    return withoutGitSuffix;
  }
}
