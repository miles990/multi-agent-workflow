# CT Compile Pipeline

## 目標

在 MAP 前把研究需求轉成可檢查的 CT stack。

## 步驟

1. 定義 research question、objective、scope、non-goals。
2. 載入 `shared/ct/taxonomy.yaml`、`shared/ct/ct-schema.yaml` 與 `shared/ct/templates/*.ct.md`。
3. 生成 `ct-stack.yaml`。
4. 生成 `eval-rubric.yaml`。
5. 生成 `risk-policy.yaml`。
6. 生成 `output-contract.md`。

## 產出位置

```text
.claude/memory/research/{topic-id}/
├── ct-stack.yaml
├── eval-rubric.yaml
├── risk-policy.yaml
└── output-contract.md
```

## `ct-stack.yaml` 範本

```yaml
topic: "Multi-CT Pipeline 是否能降低 agent drift"
mode: research-grade
ct_layers:
  base:
    constraints:
      - "不得將推論寫成已證實事實"
      - "核心 claim 必須附 evidence 或標記為 hypothesis"
  evidence:
    constraints:
      - "區分 primary evidence、secondary summary、model inference"
  experiment:
    constraints:
      - "每個假設必須有變因、對照組、評分標準"
```
