# Capstone Warden — Prompt Injection Detection via CoT Monitoring

## Overview

A prototype system that detects prompt injection attacks by inspecting
a victim LLM's output and reasoning trace using a "Warden" agent.

**Pipeline:**
```
attack prompt → victim LLM → {answer, reasoning_trace} → Warden → detected: True/False
```

## Structure

```
capstone-warden/
├── attacks/            # Attack & benign prompt datasets
├── victim/             # Victim LLM wrapper
├── warden/             # Warden implementations (rule-based, LLM-based)
├── evaluation/         # Evaluation pipeline & metrics
├── results/            # Experiment output (CSV/JSON logs)
├── config.py           # Model & API settings
└── run_experiment.py   # Entry point
```

## Warden Types

| Warden         | Method                                      |
|----------------|---------------------------------------------|
| Rule-based     | Keyword/pattern matching on output + trace  |
| LLM-based      | LLM-as-a-judge (yes/no detection prompt)    |

## Attack Types Covered

| Label              | Description                                      |
|--------------------|--------------------------------------------------|
| naive              | Direct concatenation of attack instruction       |
| ignore_previous    | "Ignore previous instructions and..."           |
| fake_completion    | Fake assistant turn to trick task completion     |
| combined           | Multiple techniques combined                     |
| benign             | Legitimate non-attack input (for FP testing)     |

## Metrics

- **ASR** — Attack Success Rate
- **TPR** — True Positive Rate (Warden correctly flags attacks)
- **FPR** — False Positive Rate (Warden incorrectly flags benign)

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # add your API key
python run_experiment.py
```
