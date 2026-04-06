import json
from pathlib import Path


def load_prompts(attack_types: list[str] | None = None) -> list[dict]:
    """Load attack prompts from JSON, optionally filtered by attack type."""
    data_path = Path(__file__).parent / "attack_prompts.json"
    with open(data_path) as f:
        prompts = json.load(f)

    if attack_types:
        prompts = [p for p in prompts if p["type"] in attack_types]

    return prompts


def load_all() -> list[dict]:
    return load_prompts()


def load_attacks_only() -> list[dict]:
    return load_prompts(attack_types=["naive", "ignore_previous", "fake_completion", "combined", "indirect"])


def load_benign_only() -> list[dict]:
    return load_prompts(attack_types=["benign"])
