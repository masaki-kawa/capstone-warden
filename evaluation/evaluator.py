"""
Evaluation pipeline.

Runs the full pipeline (attack prompt → victim → warden) for all prompts,
computes metrics (TPR, FPR, ASR), and saves results to CSV and JSON.
"""

from __future__ import annotations

import csv
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from attacks.attack_loader import load_all
from victim.model_wrapper import run_victim, ModelResponse
from warden.base_warden import WardenResult
from warden.rule_based_warden import RuleBasedWarden
from warden.llm_based_warden import LLMBasedWarden


def run_pipeline(
    use_rule_based: bool = True,
    use_llm_based: bool = True,
    attack_types: list[str] | None = None,
    dry_run: bool = False,
    model_key: str | None = None,
) -> list[dict]:
    """
    Run the full evaluation pipeline.

    Args:
        use_rule_based: Include rule-based warden.
        use_llm_based:  Include LLM-based warden.
        attack_types:   Filter prompt types (None = all).
        dry_run:        If True, skip actual API calls and use dummy data.

    Returns:
        List of result dicts (one per prompt × warden combination).
    """
    prompts = load_all()
    if attack_types:
        prompts = [p for p in prompts if p["type"] in attack_types]

    wardens: list[tuple[str, object]] = []
    if use_rule_based:
        wardens.append(("rule_based", RuleBasedWarden()))
    if use_llm_based:
        wardens.append(("llm_based", LLMBasedWarden(model_key=model_key)))

    results = []

    for i, prompt in enumerate(prompts):
        print(f"\n[{i+1}/{len(prompts)}] Running: {prompt['id']} (type={prompt['type']})")

        if dry_run:
            model_resp = _dummy_victim_response(prompt)
        else:
            try:
                model_resp = run_victim(prompt, model_key=model_key)
            except Exception as e:
                print(f"  ERROR calling victim model: {e}")
                continue

        print(f"  → Victim answer: {model_resp.final_answer[:80]}...")

        for warden_name, warden in wardens:
            if dry_run:
                warden_result = _dummy_warden_result(warden_name)
            else:
                try:
                    warden_result = warden.inspect(
                        reasoning_trace=model_resp.reasoning_trace,
                        final_answer=model_resp.final_answer,
                        original_prompt=prompt["user_prompt"],
                    )
                except Exception as e:
                    print(f"  ERROR in {warden_name} warden: {e}")
                    continue

            status = "DETECTED" if warden_result.detected else "NOT DETECTED"
            correct = warden_result.detected == bool(prompt["label"])
            print(f"  [{warden_name}] {status} | correct={correct} | {warden_result.reason[:60]}")

            results.append({
                "prompt_id": prompt["id"],
                "attack_type": prompt["type"],
                "ground_truth": prompt["label"],
                "warden": warden_name,
                "detected": int(warden_result.detected),
                "confidence": warden_result.confidence,
                "reason": warden_result.reason,
                "correct": int(correct),
                "reasoning_trace_snippet": model_resp.reasoning_trace[:200],
                "final_answer_snippet": model_resp.final_answer[:200],
            })

        time.sleep(13)  # gemini-2.5-flash free tier: 5 req/min = 12s per request

    return results


def compute_metrics(results: list[dict], warden_name: str) -> dict:
    """Compute TP, FP, FN, TN, TPR, FPR for a single warden."""
    subset = [r for r in results if r["warden"] == warden_name]

    tp = sum(1 for r in subset if r["ground_truth"] == 1 and r["detected"] == 1)
    fp = sum(1 for r in subset if r["ground_truth"] == 0 and r["detected"] == 1)
    fn = sum(1 for r in subset if r["ground_truth"] == 1 and r["detected"] == 0)
    tn = sum(1 for r in subset if r["ground_truth"] == 0 and r["detected"] == 0)

    tpr = tp / (tp + fn) if (tp + fn) > 0 else 0.0  # True Positive Rate
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0  # False Positive Rate
    asr_blocked = tp / (tp + fn) if (tp + fn) > 0 else 0.0  # attacks blocked

    return {
        "warden": warden_name,
        "TP": tp, "FP": fp, "FN": fn, "TN": tn,
        "TPR": round(tpr, 3),
        "FPR": round(fpr, 3),
        "ASR_blocked": round(asr_blocked, 3),
        "total": len(subset),
    }


def save_results(results: list[dict], output_dir: str = "results") -> str:
    """Save results to CSV and JSON, return output directory path."""
    Path(output_dir).mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # CSV
    csv_path = os.path.join(output_dir, f"results_{timestamp}.csv")
    if results:
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)

    # JSON
    json_path = os.path.join(output_dir, f"results_{timestamp}.json")
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2)

    # Metrics summary
    wardens = list({r["warden"] for r in results})
    metrics = [compute_metrics(results, w) for w in wardens]
    metrics_path = os.path.join(output_dir, f"metrics_{timestamp}.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"\nResults saved to: {output_dir}/")
    print(f"  {csv_path}")
    print(f"  {json_path}")
    print(f"  {metrics_path}")

    return output_dir


def print_summary(results: list[dict]) -> None:
    """Print a summary table to stdout."""
    wardens = list({r["warden"] for r in results})
    print("\n" + "="*60)
    print("EVALUATION SUMMARY")
    print("="*60)
    for w in wardens:
        m = compute_metrics(results, w)
        print(f"\nWarden: {m['warden'].upper()}")
        print(f"  Total prompts : {m['total']}")
        print(f"  TP={m['TP']}  FP={m['FP']}  FN={m['FN']}  TN={m['TN']}")
        print(f"  TPR (attack detection rate) : {m['TPR']:.1%}")
        print(f"  FPR (false alarm rate)      : {m['FPR']:.1%}")
        print(f"  Attacks blocked             : {m['ASR_blocked']:.1%}")
    print("="*60)


# ── Dry-run helpers ─────────────────────────────────────────────────────────

def _dummy_victim_response(prompt: dict) -> ModelResponse:
    from victim.model_wrapper import ModelResponse
    return ModelResponse(
        prompt_id=prompt["id"],
        attack_type=prompt["type"],
        label=prompt["label"],
        model_used="dry-run",
        raw_output="[DRY RUN] No API call made.",
        reasoning_trace="[DRY RUN] reasoning trace placeholder",
        final_answer="[DRY RUN] answer placeholder",
    )


def _dummy_warden_result(warden_name: str) -> WardenResult:
    from warden.base_warden import WardenResult
    return WardenResult(
        detected=False,
        confidence="low",
        reason="[DRY RUN] no inspection performed",
        warden_type=warden_name,
    )
