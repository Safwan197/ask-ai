import os

import requests

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
GEMINI_FALLBACK_MODELS = ("gemini-3.5-flash", "gemini-3.1-flash-lite")
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)
TIMEOUT = 30


class LLMError(Exception):
    """Raised when no configured LLM provider can answer a request."""


def _ask_groq(system: str, user: str) -> str:
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise LLMError("GROQ_API_KEY is missing")

    response = requests.post(
        GROQ_URL,
        headers={"Authorization": "Bearer " + key},
        json={
            "model": GROQ_MODEL,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        },
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


def _ask_gemini(system: str, user: str, model: str = GEMINI_MODEL) -> str:
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise LLMError("GEMINI_API_KEY is missing")

    response = requests.post(
        GEMINI_URL if model == GEMINI_MODEL else (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent"
        ),
        headers={"x-goog-api-key": key},
        json={
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"temperature": 0},
        },
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()


def ask_llm(system: str, user: str) -> str:
    """Send the request to Gemini, falling back on temporary overloads."""
    errors = []
    for model in (GEMINI_MODEL, *GEMINI_FALLBACK_MODELS):
        try:
            return _ask_gemini(system, user, model)
        except requests.HTTPError as error:
            if error.response is None or error.response.status_code != 503:
                raise
            errors.append(f"{model}: {error}")

    raise LLMError(" | ".join(errors))


def clean_command(text: str) -> str:
    """Remove an optional Markdown code fence from an LLM response."""
    text = text.strip()
    if not text.startswith("```"):
        return text

    opening_end = text.find("\n")
    if opening_end == -1:
        command = text[3:].strip().strip("`").strip()
        for language in ("bash", "sh", "zsh", "powershell", "pwsh", "cmd"):
            if command.startswith(language + " "):
                return command[len(language) :].strip()
        return command

    lines = text.splitlines()
    lines.pop(0)
    if lines and lines[-1].strip().startswith("```"):
        lines.pop()
    return "\n".join(lines).strip()
