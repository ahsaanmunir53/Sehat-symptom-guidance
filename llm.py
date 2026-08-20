"""
LLM client for SEHAT - supports Groq (free) and Anthropic.

Provider is auto-detected from whichever key is present:

  GROQ_API_KEY=gsk_...        -> Groq        (default model openai/gpt-oss-20b)
  ANTHROPIC_API_KEY=sk-ant-...-> Anthropic   (default model claude-fable-5)

Or set them in data/config.json:
  {"provider": "groq", "groq_api_key": "gsk_...", "model": "openai/gpt-oss-20b"}

Override the model any time with the MODEL env var.
With no key at all the app runs in demo mode.
"""

import json
import os
from pathlib import Path

import httpx

DATA_DIR = Path(__file__).parent / "data"
CONFIG_FILE = DATA_DIR / "config.json"

PROVIDERS = {
    "groq": {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        # llama-3.3-70b-versatile was decommissioned on 16 August 2026.
        # Requests to it now fail, which is what took the consultation down.
        "default_model": "openai/gpt-oss-20b",
        "console": "console.groq.com",
    },
    "anthropic": {
        "url": "https://api.anthropic.com/v1/messages",
        "default_model": "claude-fable-5",
        "console": "console.anthropic.com",
    },
}


class LLMError(Exception):
    """User-presentable API problem."""


def _file_config() -> dict:
    """Read data/config.json, with keys lower-cased.

    The file in this repo had "Groq_api_key" with a capital G while the code
    looked for "groq_api_key", so a locally configured key was silently
    ignored and the app fell back to demo mode.
    """
    try:
        raw = json.loads(CONFIG_FILE.read_text())
    except (OSError, ValueError):
        return {}
    if not isinstance(raw, dict):
        return {}
    return {str(k).lower(): v for k, v in raw.items()}


def config() -> dict:
    # The test suite runs entirely offline. It used to get there by clearing
    # the environment, which only worked while data/config.json was being
    # misread — an accident, not a switch. This is the switch.
    if os.environ.get("SEHAT_FORCE_DEMO", "").strip().lower() in ("1", "true", "yes"):
        return {"provider": "groq", "key": "", "model": "", "configured": False}

    fc = _file_config()
    groq_key = (os.environ.get("GROQ_API_KEY") or fc.get("groq_api_key") or "").strip()
    anth_key = (os.environ.get("ANTHROPIC_API_KEY") or fc.get("anthropic_api_key") or "").strip()

    forced = (os.environ.get("LLM_PROVIDER") or fc.get("provider") or "").strip().lower()
    if forced in PROVIDERS:
        provider = forced
    elif groq_key:
        provider = "groq"
    elif anth_key:
        provider = "anthropic"
    else:
        provider = "groq"

    key = groq_key if provider == "groq" else anth_key
    model = (os.environ.get("MODEL")
             or os.environ.get("ANTHROPIC_MODEL")
             or fc.get("model")
             or PROVIDERS[provider]["default_model"]).strip()

    return {"provider": provider, "key": key, "model": model, "configured": bool(key)}


def _fail(status: int, body: str, cfg: dict):
    if status == 401 or status == 403:
        raise LLMError(f"The {cfg['provider'].title()} API key was rejected. "
                       f"Check your key from {PROVIDERS[cfg['provider']]['console']}.")
    if status == 404:
        raise LLMError(f"Model '{cfg['model']}' was not found on {cfg['provider'].title()}. "
                       "Set the MODEL environment variable to a model your account can use.")
    if status == 429:
        raise LLMError("Rate limit reached on the free tier. Wait a minute and try again.")
    detail = ""
    try:
        detail = json.loads(body).get("error", {}).get("message", "")[:200]
    except (ValueError, AttributeError):
        detail = body[:200]
    raise LLMError(f"AI service error {status}. {detail}".strip())


def _post(url: str, headers: dict, payload: dict) -> httpx.Response:
    try:
        return httpx.post(url, headers=headers, json=payload, timeout=90.0)
    except httpx.HTTPError as exc:
        raise LLMError(f"Could not reach the AI service ({exc.__class__.__name__}). "
                       "Check your internet connection and try again.") from exc


def _call_groq(cfg: dict, system: str, messages: list, max_tokens: int) -> str:
    url = PROVIDERS["groq"]["url"]
    headers = {"Authorization": f"Bearer {cfg['key']}", "Content-Type": "application/json"}
    model = cfg["model"]
    payload = {
        "model": model,
        "temperature": 0.3,
        "messages": [{"role": "system", "content": system}] + messages,
        "response_format": {"type": "json_object"},
    }
    if "gpt-oss" in model or "qwen3" in model:
        # Reasoning models spend tokens thinking before they write. Budget
        # only for the answer and "content" comes back empty — a 200 with
        # nothing in it. Give the reasoning room, and keep it out of the reply.
        payload["max_completion_tokens"] = max(max_tokens, 2500)
        payload["reasoning_effort"] = "low"
        payload["include_reasoning"] = False
    else:
        payload["max_tokens"] = max_tokens
    r = _post(url, headers, payload)
    # not every Groq model supports JSON mode - retry plainly if that's the complaint
    if r.status_code == 400 and "response_format" in r.text:
        payload.pop("response_format")
        r = _post(url, headers, payload)
    if r.status_code >= 400:
        _fail(r.status_code, r.text, cfg)
    try:
        text = r.json()["choices"][0]["message"].get("content") or ""
    except (KeyError, IndexError, ValueError) as exc:
        raise LLMError("The AI service returned an unexpected reply.") from exc
    if not text.strip():
        # Almost always a reasoning model that ran out of completion budget.
        raise LLMError(f"Model '{cfg['model']}' returned an empty reply. "
                       "If it is a reasoning model, it needs a larger token "
                       "budget.")
    return text


def _call_anthropic(cfg: dict, system: str, messages: list, max_tokens: int) -> str:
    url = PROVIDERS["anthropic"]["url"]
    headers = {
        "x-api-key": cfg["key"],
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {"model": cfg["model"], "max_tokens": max_tokens,
               "system": system, "messages": messages}
    r = _post(url, headers, payload)
    if r.status_code >= 400:
        _fail(r.status_code, r.text, cfg)
    data = r.json()
    return "".join(b.get("text", "") for b in data.get("content", [])
                   if b.get("type") == "text")


def call_llm(system: str, messages: list, max_tokens: int = 1600) -> str:
    """One non-streaming completion. Returns the model's text."""
    cfg = config()
    if not cfg["configured"]:
        raise LLMError("not_configured")
    if cfg["provider"] == "groq":
        return _call_groq(cfg, system, messages, max_tokens)
    return _call_anthropic(cfg, system, messages, max_tokens)


# backwards-compatible alias
call_claude = call_llm
