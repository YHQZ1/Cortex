from dataclasses import dataclass
from collections.abc import Awaitable, Callable
from pathlib import PurePosixPath
from urllib.parse import quote

import httpx

from app.config import Settings
from app.pipeline.documents import SourceDocument
from app.pipeline.filtering import get_path_skip_reason


@dataclass(frozen=True)
class FetchedRepository:
    source_ref: str
    name: str
    default_branch: str
    documents: list[SourceDocument]
    diagnostics: "GitHubFetchDiagnostics"


@dataclass(frozen=True)
class GitHubFetchDiagnostics:
    discovered_files: int
    candidate_files: int
    fetched_documents: int
    ignored_by_reason: dict[str, int]
    fetch_skipped_files: int = 0
    truncated_files: int = 0


class GitHubProviderError(RuntimeError):
    pass


class GitHubProvider:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def fetch_repository(
        self,
        source_ref: str,
        progress_callback: Callable[[str, int, int], Awaitable[None]] | None = None,
    ) -> FetchedRepository:
        owner, repo = self._parse_source_ref(source_ref)
        if progress_callback is not None:
            await progress_callback("fetching repository metadata", 0, 1)

        async with httpx.AsyncClient(
            base_url=self._settings.github_api_url,
            headers=self._headers(),
            timeout=self._settings.github_fetch_timeout_seconds,
        ) as client:
            repo_payload = await self._get_json(client, f"/repos/{owner}/{repo}")
            default_branch = repo_payload["default_branch"]
            tree_payload = await self._get_json(
                client,
                f"/repos/{owner}/{repo}/git/trees/{quote(default_branch)}",
                params={"recursive": "1"},
            )
        if progress_callback is not None:
            await progress_callback("filtering repository files", 0, 1)

        blob_paths = [
            item["path"]
            for item in tree_payload.get("tree", [])
            if item.get("type") == "blob"
        ]
        candidate_paths: list[str] = []
        ignored_by_reason: dict[str, int] = {}
        for path in blob_paths:
            reason = get_path_skip_reason(path)
            if reason is None:
                candidate_paths.append(path)
            else:
                ignored_by_reason[reason] = ignored_by_reason.get(reason, 0) + 1

        truncated_files = max(0, len(candidate_paths) - self._settings.github_max_files_per_repo)
        candidate_paths = candidate_paths[: self._settings.github_max_files_per_repo]
        if progress_callback is not None:
            await progress_callback("fetching files", 0, len(candidate_paths))

        documents, fetch_skipped_files = await self._fetch_documents(
            owner=owner,
            repo=repo,
            branch=default_branch,
            paths=candidate_paths,
            progress_callback=progress_callback,
        )

        return FetchedRepository(
            source_ref=f"{owner}/{repo}",
            name=repo,
            default_branch=default_branch,
            documents=documents,
            diagnostics=GitHubFetchDiagnostics(
                discovered_files=len(blob_paths),
                candidate_files=len(candidate_paths),
                fetched_documents=len(documents),
                ignored_by_reason=ignored_by_reason,
                fetch_skipped_files=fetch_skipped_files,
                truncated_files=truncated_files,
            ),
        )

    async def _fetch_documents(
        self,
        *,
        owner: str,
        repo: str,
        branch: str,
        paths: list[str],
        progress_callback: Callable[[str, int, int], Awaitable[None]] | None = None,
    ) -> tuple[list[SourceDocument], int]:
        async with httpx.AsyncClient(
            headers=self._headers(),
            timeout=self._settings.github_fetch_timeout_seconds,
            follow_redirects=True,
        ) as client:
            documents: list[SourceDocument] = []
            skipped_files = 0
            for index, path in enumerate(paths, start=1):
                url = self._raw_file_url(owner=owner, repo=repo, branch=branch, path=path)
                response = await client.get(url)
                if response.status_code in {400, 404}:
                    skipped_files += 1
                    if progress_callback is not None:
                        await progress_callback("fetching files", index, len(paths))
                    continue
                response.raise_for_status()

                content_type = response.headers.get("content-type", "")
                if "text" not in content_type and "json" not in content_type:
                    skipped_files += 1
                    if progress_callback is not None:
                        await progress_callback("fetching files", index, len(paths))
                    continue

                documents.append(SourceDocument(path=path, content=response.text))
                if progress_callback is not None:
                    await progress_callback("fetching files", index, len(paths))

        return documents, skipped_files

    def _raw_file_url(self, *, owner: str, repo: str, branch: str, path: str) -> str:
        encoded_path = "/".join(quote(part) for part in PurePosixPath(path).parts)
        encoded_branch = quote(branch, safe="")
        return f"{self._settings.github_raw_url}/{owner}/{repo}/{encoded_branch}/{encoded_path}"

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "cortex-api",
        }
        if self._settings.github_token:
            headers["Authorization"] = f"Bearer {self._settings.github_token}"
        return headers

    async def _get_json(
        self,
        client: httpx.AsyncClient,
        path: str,
        *,
        params: dict[str, str] | None = None,
    ) -> dict:
        response = await client.get(path, params=params)
        if response.status_code == 404:
            raise GitHubProviderError(f"GitHub repository or resource not found: {path}")
        response.raise_for_status()
        return response.json()

    def _parse_source_ref(self, source_ref: str) -> tuple[str, str]:
        parts = source_ref.strip().strip("/").split("/")
        if len(parts) != 2 or not all(parts):
            raise GitHubProviderError("GitHub source_ref must use the format 'owner/repo'.")
        return parts[0], parts[1]
