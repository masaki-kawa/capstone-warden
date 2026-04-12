# CLAUDE.md — capstone-warden

UTS Capstone プロジェクト。Chain-of-Thought（CoT）の推論トレースを監視することで
Prompt Injection 攻撃を検出する「Warden」エージェントの研究実装。

---

## アーキテクチャ

```
attack prompt（攻撃 or 良性）
        ↓  victim/
    Victim LLM（answer + reasoning_trace を出力）
        ↓  warden/
    Warden（ルールベース or LLMベース）
        ↓
    detected: True / False
        ↓  evaluation/
    ASR / TPR / FPR の集計
        ↓
    results/ に CSV / JSON で保存
```

---

## ディレクトリ構成

```
capstone-warden/
├── run_experiment.py        # エントリーポイント
├── config.py                # モデル・APIキー設定
├── attacks/
│   ├── attack_prompts.json  # 攻撃プロンプトデータセット
│   └── attack_loader.py
├── victim/                  # Victim LLMラッパー
├── warden/
│   ├── base_warden.py
│   ├── rule_based_warden.py   # キーワード/パターンマッチング
│   └── llm_based_warden.py    # LLM-as-a-judge
├── evaluation/              # 評価パイプライン・メトリクス
└── results/                 # 実験結果（CSV/JSON）← 生成物
```

---

## よく使うコマンド

```bash
# 仮想環境の有効化
source .venv/bin/activate  # または python3 -m venv .venv && source .venv/bin/activate

# 実験実行
python run_experiment.py

# 依存関係インストール
pip install -r requirements.txt
```

---

## 攻撃タイプ

| ラベル | 説明 |
|--------|------|
| `naive` | 攻撃命令の直接連結 |
| `ignore_previous` | "Ignore previous instructions and..." |
| `fake_completion` | 偽のアシスタントターンでタスク完了を偽装 |
| `combined` | 複数テクニックの組み合わせ |
| `benign` | 正常入力（FP検証用） |

## 評価指標

| 指標 | 意味 |
|------|------|
| ASR | Attack Success Rate — 攻撃が成功した割合 |
| TPR | True Positive Rate — Wardenが攻撃を正しく検出した割合 |
| FPR | False Positive Rate — Wardenが良性を誤検出した割合 |

---

## 注意事項

- `results/` は実験結果の生成物。**削除・上書きしない**（論文の根拠データ）
- `attacks/attack_prompts.json` には意図的な悪意あるプロンプトが含まれる。**これは研究目的**であり正常
- `.env` にはAPIキーが含まれる。コミット禁止
- `__pycache__/` は変更しない
