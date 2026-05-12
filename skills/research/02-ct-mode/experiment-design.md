# Evaluation Design

## 目標

為 CT 假設建立可重跑的評估設計。

## 必填欄位

```yaml
eval_case:
  id: E001
  prompt: string
  control_condition: string
  treatment_condition: string
  expected_observation: string
  metrics:
    - constraint_compliance_rate
    - unsupported_claim_rate
    - drift_event_count
  pass_criteria:
    evidence_coverage: ">= 0.8"
    hypothesis_testability_score: ">= 0.7"
```

## 設計原則

- 控制組與實驗組只改變 CT 條件。
- 指標必須能從報告或 action logs 中抽取。
- 至少包含一個容易誘發 drift 的壓力案例。

## 必須實作 Experiment Harness

CT-experiment 不只產生研究設計，還必須產生可重跑的實驗骨架。

輸出到：

```text
.claude/memory/research/{topic-id}/experiments/ct-drift-benchmark/
├── cases.yaml
├── run-config.yaml
├── rubric.yaml
├── results.jsonl
└── analysis.md
```

建議從共用模板複製：

```text
_shared/ct/experiment-harness/cases.template.yaml
_shared/ct/experiment-harness/run-config.template.yaml
_shared/ct/experiment-harness/rubric.template.yaml
```

評分工具：

```bash
python3 _shared/ct/experiment-harness/score-run.py \
  --run-dir .claude/memory/research/{topic-id} \
  --condition ct_experiment_closed_loop \
  --case-id CTD-001 \
  --output .claude/memory/research/{topic-id}/experiments/ct-drift-benchmark/results.jsonl

python3 _shared/ct/experiment-harness/analyze-results.py \
  --results .claude/memory/research/{topic-id}/experiments/ct-drift-benchmark/results.jsonl \
  --output .claude/memory/research/{topic-id}/experiments/ct-drift-benchmark/analysis.md
```

最小條件組：

- `no_ct`
- `ct_lite`
- `ct_strict`
- `ct_experiment`
- `ct_experiment_closed_loop`

如果當下不能實際跑全部條件，仍必須產生 harness，並至少對本次 condition 跑一次 `score-run.py`。
