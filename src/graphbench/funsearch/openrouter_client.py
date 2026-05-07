from __future__ import annotations

import json
import os
from urllib import request, error


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def call_openrouter(
    messages: list[dict[str, str]],
    model: str | None = None,
    reasoning_effort: str | None = None,
    max_tokens: int = 5000,
    temperature: float = 0.8,
    response_format: dict[str, object] | None = None,
    require_parameters: bool = False,
    plugins: list[dict[str, str]] | None = None,
) -> str:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set.")

    payload: dict[str, object] = {
        "model": model or os.environ.get("OPENROUTER_MODEL", "openai/gpt-5.5"),
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    effort = reasoning_effort or os.environ.get("OPENROUTER_REASONING_EFFORT", "low")
    if effort:
        payload["reasoning"] = {"effort": effort}
    if response_format is not None:
        payload["response_format"] = response_format
    if require_parameters:
        payload["provider"] = {"require_parameters": True}
    if plugins:
        payload["plugins"] = plugins

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": os.environ.get("OPENROUTER_HTTP_REFERER", "https://github.com/graphbench-project"),
        "X-OpenRouter-Title": os.environ.get("OPENROUTER_X_TITLE", "GraphBench FunSearch"),
    }
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(OPENROUTER_URL, data=data, headers=headers, method="POST")

    try:
        with request.urlopen(req, timeout=120) as response:
            body = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenRouter request failed with HTTP {exc.code}: {detail}") from exc

    return body["choices"][0]["message"]["content"]
