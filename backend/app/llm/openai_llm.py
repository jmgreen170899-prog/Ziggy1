# app/llm/openai_llm.py
import os
from typing import Any

import httpx


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE = os.getenv("OPENAI_BASE", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # fast, tool-friendly


class OpenAILLM:
    def __init__(self, model: str | None = None):
        self.model = model or OPENAI_MODEL
        self.client = httpx.Client(
            base_url=OPENAI_BASE,
            timeout=60.0,
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
        )

    def chat(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None
    ) -> dict[str, Any]:
        """
        Returns assistant message; if tool call is suggested, returns it in message['tool_calls'].
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        r = self.client.post("/chat/completions", json=payload)
        r.raise_for_status()
        data = r.json()
        choice = data["choices"][0]["message"]
        return choice
