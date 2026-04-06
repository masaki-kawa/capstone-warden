"""
Victim LLM wrapper.

Supports three backends:
  - ollama  → Llama 3.2 / Qwen 2.5 running locally via Ollama
  - gemini  → Google Gemini Flash (free API)

Returns:
  - reasoning_trace : CoT surrogate (REASONING section)
  - final_answer    : model's answer (ANSWER section)

Since true internal CoT tokens are not accessible via any of these APIs,
we use a CoT surrogate: the system prompt instructs the model to write its
step-by-step reasoning explicitly before giving the final answer.
"""

from __future__ import annotations

from dataclasses import dataclass


COT_INSTRUCTION = (
    "Before answering, think through your reasoning step by step. "
    "Format your response exactly as:\n"
    "REASONING:\n<your step-by-step reasoning here>\n\n"
    "ANSWER:\n<your final answer here>"
)


@dataclass
class ModelResponse:
    prompt_id: str
    attack_type: str
    label: int
    model_used: str
    raw_output: str
    reasoning_trace: str
    final_answer: str


def _parse_cot_output(raw: str) -> tuple[str, str]:
    """Split raw output into (reasoning_trace, final_answer)."""
    reasoning = ""
    answer = raw

    if "REASONING:" in raw and "ANSWER:" in raw:
        parts = raw.split("ANSWER:", 1)
        answer = parts[1].strip()
        reasoning = parts[0].replace("REASONING:", "", 1).strip()
    elif "REASONING:" in raw:
        reasoning = raw.replace("REASONING:", "", 1).strip()
        answer = ""

    return reasoning, answer


# ── Ollama backend ────────────────────────────────────────────────────────────

def _run_ollama(system_prompt: str, user_prompt: str, model_name: str, base_url: str) -> str:
    """Call a local Ollama model and return raw text output."""
    import urllib.request
    import json

    payload = json.dumps({
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "options": {"temperature": 0},
    }).encode()

    req = urllib.request.Request(
        f"{base_url}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())

    return data["message"]["content"]


# ── Gemini backend ────────────────────────────────────────────────────────────

def _run_gemini(system_prompt: str, user_prompt: str, model_name: str) -> str:
    """Call Google Gemini Flash and return raw text output. Retries on rate limit."""
    import os
    import time
    from google import genai
    from google.genai import types
    from dotenv import load_dotenv
    load_dotenv()

    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY", ""))

    for attempt in range(5):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0,
                ),
            )
            return response.text
        except Exception as e:
            if "429" in str(e) and attempt < 4:
                wait = 15 * (attempt + 1)
                print(f"  Rate limited — waiting {wait}s before retry ({attempt+1}/4)...")
                time.sleep(wait)
            else:
                raise


# ── Public interface ──────────────────────────────────────────────────────────

def run_victim(prompt: dict, model_key: str | None = None) -> ModelResponse:
    """
    Run a single prompt through the victim model.

    Args:
        prompt:    A dict from attack_prompts.json
        model_key: "llama", "qwen", or "gemini" (overrides config default)
    """
    from config import VICTIM_MODEL, MODEL_CONFIG

    key = model_key or VICTIM_MODEL
    cfg = MODEL_CONFIG[key]

    system_with_cot = prompt["system_prompt"] + "\n\n" + COT_INSTRUCTION

    if cfg["provider"] == "ollama":
        raw = _run_ollama(
            system_prompt=system_with_cot,
            user_prompt=prompt["user_prompt"],
            model_name=cfg["model_name"],
            base_url=cfg["base_url"],
        )
    elif cfg["provider"] == "gemini":
        raw = _run_gemini(
            system_prompt=system_with_cot,
            user_prompt=prompt["user_prompt"],
            model_name=cfg["model_name"],
        )
    else:
        raise ValueError(f"Unknown provider: {cfg['provider']}")

    reasoning_trace, final_answer = _parse_cot_output(raw)

    return ModelResponse(
        prompt_id=prompt["id"],
        attack_type=prompt["type"],
        label=prompt["label"],
        model_used=f"{key}/{cfg['model_name']}",
        raw_output=raw,
        reasoning_trace=reasoning_trace,
        final_answer=final_answer,
    )
