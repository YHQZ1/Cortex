import json
from collections.abc import AsyncIterator

import httpx

from app.config import Settings


class OllamaLLMProvider:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def generate_answer(self, *, question: str, context: str) -> str:
        prompt = _build_prompt(question=question, context=context)
        return await self._complete(prompt)

    async def generate_general_answer(self, *, question: str) -> str:
        prompt = _build_general_prompt(question=question)
        return await self._complete(prompt)

    async def _complete(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self._settings.ollama_url}/v1/chat/completions",
                json={
                    "model": self._settings.llm_model,
                    "stream": False,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            response.raise_for_status()

        data = response.json()
        choices = data.get("choices", [])
        content = choices[0].get("message", {}).get("content") if choices else None
        if not isinstance(content, str):
            raise ValueError("Ollama chat response did not include answer content.")
        return content.strip()

    async def stream_answer(self, *, question: str, context: str) -> AsyncIterator[str]:
        prompt = _build_prompt(question=question, context=context)
        async for token in self._stream_complete(prompt):
            yield token

    async def stream_general_answer(self, *, question: str) -> AsyncIterator[str]:
        prompt = _build_general_prompt(question=question)
        async for token in self._stream_complete(prompt):
            yield token

    async def _stream_complete(self, prompt: str) -> AsyncIterator[str]:
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                f"{self._settings.ollama_url}/v1/chat/completions",
                json={
                    "model": self._settings.llm_model,
                    "stream": True,
                    "messages": [{"role": "user", "content": prompt}],
                },
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue

                    payload = line.removeprefix("data: ").strip()
                    if payload == "[DONE]":
                        break

                    data = json.loads(payload)
                    choices = data.get("choices", [])
                    delta = choices[0].get("delta", {}) if choices else {}
                    content = delta.get("content")
                    if isinstance(content, str):
                        yield content


def _build_prompt(*, question: str, context: str) -> str:
    return (
        "You are Cortex, a codebase analysis assistant.\n"
        "Answer in clear English using only the provided context.\n"
        "If the context is insufficient, say what is missing.\n"
        "Mention relevant files naturally when useful.\n\n"
        f"Question:\n{question}\n\n"
        f"Retrieved context:\n{context}\n\n"
        "Answer:"
    )


def _build_general_prompt(*, question: str) -> str:
    return (
        "You are Cortex, a helpful local assistant.\n"
        "Answer the user's general question clearly and concisely. "
        "Do not cite repository sources unless the user asks about indexed repository context.\n\n"
        f"Question:\n{question}\n\n"
        "Answer:"
    )
