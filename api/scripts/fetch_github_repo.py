import asyncio
import sys

from app.config import get_settings
from app.providers.github import GitHubProvider


async def main() -> None:
    source_ref = sys.argv[1] if len(sys.argv) > 1 else "YHQZ1/Cortex"
    max_files = int(sys.argv[2]) if len(sys.argv) > 2 else 25

    settings = get_settings()
    settings.github_max_files_per_repo = max_files

    print(f"Fetching {source_ref} with max_files={max_files}...", flush=True)
    provider = GitHubProvider(settings)
    repository = await provider.fetch_repository(source_ref)

    print(f"source_ref={repository.source_ref}")
    print(f"name={repository.name}")
    print(f"default_branch={repository.default_branch}")
    print(f"documents={len(repository.documents)}")
    for document in repository.documents[:10]:
        print(f"- {document.path} ({len(document.content.encode('utf-8'))} bytes)")


if __name__ == "__main__":
    asyncio.run(main())
