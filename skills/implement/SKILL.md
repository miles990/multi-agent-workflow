---
name: implement
version: 3.0.0
description: 多 Agent 監督式實作框架 - TDD 驅動、即時審查、品質守護
triggers: [multi-implement, parallel-implement, 監督實作]
---

# Multi-Agent Implement v3.0.0

> TDD 閘門 → 並行實作 → 即時審查 → 品質守護

## 使用方式

```bash
/multi-implement [任務路徑]
/multi-implement .claude/memory/tasks/user-auth/tasks.yaml
```

**Flags**: `--from-tasks ID` | `--skip-tdd-check` | `--parallel N`

## 角色配置

| ID | 名稱 | 模型 | 聚焦 |
|----|------|------|------|
| `main_agent` | 主實作者 | sonnet | 功能實作 |
| `tdd-enforcer` | TDD 守護者 | haiku | 測試先行檢查 |
| `security-auditor` | 安全審計員 | sonnet | 安全漏洞檢測 |
| `maintainer` | 可維護性審查 | haiku | 程式碼品質 |

→ 模型路由配置：[shared/config/model-routing.yaml](../../shared/config/model-routing.yaml)

## 執行流程

```
Phase 0: 載入任務 → 解析 tasks.yaml、排序 waves
    ↓
For each task in waves:
    ↓
    Phase 1: TDD 閘門（PRE-TASK）
    ├── 測試檔案存在？
    ├── 測試可執行？
    └── ❌ 失敗 → BLOCKER，無法繼續
    ↓
    Phase 2: 並行實作 + 審查
    ┌──────────┬──────────┬──────────┐
    │ 主實作者 │安全審計員│可維護性  │
    └──────────┴──────────┴──────────┘
    ↓
    Phase 3: TDD 閘門（POST-TASK）
    ├── 測試通過？
    └── 覆蓋率達標？
    ↓
    Phase 4: 自我審查 + 提交
    ↓
End for
    ↓
Phase 5: 品質閘門 → 整體驗證
```

## TDD 強制閘門

**Pre-Task Gate（BLOCKER）**：
- 測試檔案必須存在
- 測試必須可執行（即使失敗）

**Post-Task Gate（BLOCKER）**：
- 測試必須通過
- 覆蓋率 ≥ 80%

**驗證腳本**：`shared/tools/tdd-validator.sh`

→ 配置：[shared/quality/tdd-enforcement.yaml](../../shared/quality/tdd-enforcement.yaml)

## 安全審計

使用 OWASP Top 10 和 CWE Top 25 框架：
- SQL Injection
- XSS
- 認證/授權問題
- 敏感資料處理

→ 框架：[shared/perspectives/expertise-frameworks/security.yaml](../../shared/perspectives/expertise-frameworks/security.yaml)

## 品質閘門

通過條件（IMPLEMENT 階段）：
- ✅ 所有任務完成
- ✅ 測試通過
- ✅ 無 BLOCKER 問題
- ✅ 品質分數 ≥ 80

→ 閘門配置：[shared/quality/gates.yaml](../../shared/quality/gates.yaml)

## 輸出結構

```
.claude/memory/implement/[tasks-id]/
├── meta.yaml           # 元數據
├── task-results/       # 每個任務的結果
│   ├── T-F-001.yaml
│   └── T-F-002.yaml
├── security-report.md  # 安全審計報告
├── coverage-report.md  # 覆蓋率報告
└── summary.md          # 實作摘要
```

## 共用模組

| 模組 | 用途 |
|------|------|
| [quality/tdd-enforcement.yaml](../../shared/quality/tdd-enforcement.yaml) | TDD 強制 |
| [quality/gates.yaml](../../shared/quality/gates.yaml) | 品質閘門 |
| [perspectives/expertise-frameworks/security.yaml](../../shared/perspectives/expertise-frameworks/security.yaml) | 安全框架 |
| [tools/tdd-validator.sh](../../shared/tools/tdd-validator.sh) | TDD 驗證器 |

## 工作流位置

```
RESEARCH → PLAN → TASKS → IMPLEMENT → REVIEW → VERIFY
                              ↑
                           你在這裡
```

- **輸入**：`tasks.yaml` 來自 `tasks` skill
- **輸出**：已實作的程式碼，供 `review` skill 審查
