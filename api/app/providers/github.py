from dataclasses import dataclass
from pathlib import PurePosixPath
from urllib.parse import quote

import httpx

from app.config import Settings
from app.pipeline.documents import SourceDocument
from app.pipeline.filtering import ALLOWED_EXTENSIONS, SKIPPED_FILENAMES, SKIPPED_PATH_PARTS


@dataclass(frozen=True)
class FetchedRepository:
    source_ref: str
    name: str
    default_branch: str
    documents: list[SourceDocument]


class GitHubProviderError(RuntimeError):
    pass


class GitHubProvider:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def fetch_repository(self, source_ref: str) -> FetchedRepository:
        owner, repo = self._parse_source_ref(source_ref)

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

        candidate_paths = [
            item["path"]
            for item in tree_payload.get("tree", [])
            if item.get("type") == "blob" and self._is_candidate_path(item.get("path", ""))
        ][: self._settings.github_max_files_per_repo]

        documents = await self._fetch_documents(
            owner=owner,
            repo=repo,
            branch=default_branch,
            paths=candidate_paths,
        )

        return FetchedRepository(
            source_ref=f"{owner}/{repo}",
            name=repo,
            default_branch=default_branch,
            documents=documents,
        )

    async def _fetch_documents(
        self,
        *,
        owner: str,
        repo: str,
        branch: str,
        paths: list[str],
    ) -> list[SourceDocument]:
        async with httpx.AsyncClient(
            headers=self._headers(),
            timeout=self._settings.github_fetch_timeout_seconds,
            follow_redirects=True,
        ) as client:
            documents: list[SourceDocument] = []
            for path in paths:
                url = self._raw_file_url(owner=owner, repo=repo, branch=branch, path=path)
                response = await client.get(url)
                if response.status_code in {400, 404}:
                    continue
                response.raise_for_status()

                content_type = response.headers.get("content-type", "")
                if "text" not in content_type and "json" not in content_type:
                    continue

                documents.append(SourceDocument(path=path, content=response.text))

        return documents

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

    def _is_candidate_path(self, path_value: str) -> bool:
        path = PurePosixPath(path_value)
        if any(part in SKIPPED_PATH_PARTS for part in path.parts):
            return False
        if path.name in SKIPPED_FILENAMES:
            return False
        return path.suffix.lower() in ALLOWED_EXTENSIONS
