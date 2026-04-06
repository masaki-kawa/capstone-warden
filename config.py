import os

# ── API Keys (set via .env) ──────────────────────────────────────────────────
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# ── Available victim models ──────────────────────────────────────────────────
# "llama"  → Ollama (local) Llama 3.2
# "qwen"   → Ollama (local) Qwen 2.5
# "gemini" → Google Gemini Flash (free API)
VICTIM_MODEL = os.getenv("VICTIM_MODEL", "gemini")  # default: gemini

MODEL_CONFIG = {
    "llama": {
        "provider": "ollama",
        "model_name": "llama3.2",
        "base_url": "http://localhost:11434",
    },
    "qwen": {
        "provider": "ollama",
        "model_name": "qwen2.5",
        "base_url": "http://localhost:11434",
    },
    "gemini": {
        "provider": "gemini",
        "model_name": "gemini-2.5-flash",
    },
}

# ── Warden model (LLM-based warden uses same victim model by default) ────────
WARDEN_MODEL = os.getenv("WARDEN_MODEL", VICTIM_MODEL)

# ── Results ──────────────────────────────────────────────────────────────────
RESULTS_DIR = "results"
