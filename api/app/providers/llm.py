import httpx

from app.config import Settings


class OllamaLLMProvider:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def generate_answer(self, *, question: str, context: str) -> str:
        prompt = (
            "You are Cortex, a codebase analysis assistant.\n"
            "Answer in clear English using only the provided context.\n"
            "If the context is insufficient, say what is missing.\n"
            "Mention relevant files naturally when useful.\n\n"
            f"Question:\n{question}\n\n"
            f"Retrieved context:\n{context}\n\n"
            "Answer:"
        )
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
