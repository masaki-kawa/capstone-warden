"""
Main entry point for the Warden prototype evaluation.

Usage:
    python3 run_experiment.py                          # gemini + both wardens
    python3 run_experiment.py --model llama            # Ollama Llama 3.2
    python3 run_experiment.py --model qwen             # Ollama Qwen 2.5
    python3 run_experiment.py --model gemini           # Gemini Flash (default)
    python3 run_experiment.py --rule-only              # rule-based warden only
    python3 run_experiment.py --llm-only               # LLM-based warden only
    python3 run_experiment.py --dry-run                # no API calls (structure test)
    python3 run_experiment.py --types naive benign     # filter attack types
"""

import argparse
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

from evaluation.evaluator import run_pipeline, save_results, print_summary


def main():
    parser = argparse.ArgumentParser(description="Warden Prototype Experiment Runner")
    parser.add_argument("--model", choices=["llama", "qwen", "gemini"], default=None,
                        help="Victim model to use (default: from config.py)")
    parser.add_argument("--dry-run", action="store_true", help="Skip API calls (structure test)")
    parser.add_argument("--rule-only", action="store_true", help="Rule-based warden only")
    parser.add_argument("--llm-only", action="store_true", help="LLM-based warden only")
    parser.add_argument("--types", nargs="+", default=None,
                        help="Attack types to include (e.g. naive ignore_previous benign)")
    args = parser.parse_args()

    # Override model in config if specified
    if args.model:
        import config
        config.VICTIM_MODEL = args.model
        config.WARDEN_MODEL = args.model

    from config import VICTIM_MODEL
    use_rule = not args.llm_only
    use_llm = not args.rule_only

    print("=" * 60)
    print("WARDEN PROTOTYPE — PROMPT INJECTION DETECTION")
    print("=" * 60)
    print(f"  Victim model : {VICTIM_MODEL}")
    print(f"  Wardens      : {'rule_based ' if use_rule else ''}{'llm_based' if use_llm else ''}")
    print(f"  Dry run      : {args.dry_run}")
    print(f"  Attack filter: {args.types or 'all'}")
    print()

    results = run_pipeline(
        use_rule_based=use_rule,
        use_llm_based=use_llm,
        attack_types=args.types,
        dry_run=args.dry_run,
        model_key=args.model,
    )

    if results:
        print_summary(results)
        save_results(results)
    else:
        print("No results generated. Check errors above.")


if __name__ == "__main__":
    main()
