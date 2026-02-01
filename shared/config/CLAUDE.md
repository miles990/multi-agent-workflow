# Configuration System

> 統一配置索引與查詢系統

## 概述

本目錄包含 Multi-Agent Workflow 的核心配置系統，採用集中式索引管理所有配置檔案的元資料、位置和相互依賴關係。

```
shared/config/
├── INDEX.yaml              # 統一配置索引（核心）
├── CLAUDE.md               # 本文檔
├── execution-profiles.yaml # 執行模式配置
├── model-routing.yaml      # 模型路由策略
├── parallel-execution.yaml # 並行執行策略
├── context-freshness.yaml  # 上下文新鮮機制
├── context-budget.yaml     # Token 預算分配
├── early-termination.yaml  # 早期終止條件
├── stage-handoff.yaml      # 階段傳遞協議
├── thinking-triggers.yaml  # 擴展思考觸發
├── commit-settings.yaml    # Git Commit 設定
├── chunking.yaml           # 大任務分塊處理
├── prompt-loading.yaml     # 分層載入機制
└── result-compression.yaml # 結果壓縮規則
```

## 配置分類

| 分類 | 說明 | 數量 |
|------|------|------|
| `skill-config` | Skill 定義和 frontmatter - 觸發條件、工具權限、執行流程 | 10 |
| `perspective-config` | 視角配置 - 各階段可用視角、模型路由、組合規則 | 5 |
| `quality-config` | 品質控制 - 閘門、評分標準、TDD 強制、回退策略 | 6 |
| `coordination-config` | 協調配置 - 並行執行、依賴偵測、Context 管理 | 8 |
| `integration-config` | 整合配置 - 外部工具、Hooks、Commit 規則 | 3 |
| `metrics-config` | 指標配置 - 執行、品質、效率指標定義 | 1 |
| `schema-config` | Schema 定義 - 資料結構驗證 | 1 |
| `expertise-config` | 專業知識框架 - 安全、架構、測試、效能 | 4 |
| `plugin-config` | Plugin 配置 - 插件元資料、marketplace | 2 |

## INDEX.yaml 結構

### 版本與元資料

```yaml
version: "1.0.0"           # 索引版本
last_updated: "2026-02-01" # 最後更新日期
generated_by: "..."        # 產生來源
```

### categories 區段

定義所有配置分類：

```yaml
categories:
  - id: skill-config           # 唯一識別碼
    description: "..."         # 分類說明
    icon: "lightning"          # 顯示圖示
    count: 10                  # 配置數量
```

### entries 區段

每個配置條目包含：

```yaml
entries:
  - path: skills/research/SKILL.md  # 相對於專案根目錄的路徑
    type: skill-config              # 所屬分類
    description: "..."              # 配置用途說明
    keys:                           # 關鍵欄位
      - name: research              # 配置名稱
      - version: "3.2.0"            # 版本
      - triggers: [...]             # 觸發關鍵字
      - model: sonnet               # 使用模型
    references:                     # 依賴的其他配置
      - shared/config/model-routing.yaml
      - shared/quality/gates.yaml
```

### references 說明

`references` 欄位列出該配置依賴或引用的其他配置檔案：

- 空陣列 `[]` 表示無依賴
- 路徑使用相對於專案根目錄的格式
- 可以引用目錄（如 `shared/perspectives/expertise-frameworks/`）

## 使用指南

### 使用 get-config.sh 查詢工具

```bash
# 列出所有分類
./scripts/get-config.sh --list-categories

# 列出特定分類的配置
./scripts/get-config.sh --category skill-config
./scripts/get-config.sh --category quality-config

# 搜尋配置（模糊匹配）
./scripts/get-config.sh --search "tdd"
./scripts/get-config.sh --search "parallel"
./scripts/get-config.sh --search "security"

# 顯示特定配置詳情
./scripts/get-config.sh --show skills/implement/SKILL.md
./scripts/get-config.sh --show shared/quality/gates.yaml

# 顯示配置關係圖
./scripts/get-config.sh --relations
```

### 使用 yq 直接查詢

```bash
# 列出所有 skill-config 路徑
yq '.entries[] | select(.type == "skill-config") | .path' shared/config/INDEX.yaml

# 查找特定配置的引用
yq '.entries[] | select(.path == "shared/quality/gates.yaml") | .references' shared/config/INDEX.yaml

# 列出所有有 references 的配置
yq '.entries[] | select(.references | length > 0) | .path' shared/config/INDEX.yaml

# 搜尋包含特定關鍵字的配置
yq '.entries[] | select(.description | contains("TDD")) | .path' shared/config/INDEX.yaml
```

### 範例查詢場景

| 場景 | 命令 |
|------|------|
| 找 TDD 相關配置 | `./scripts/get-config.sh --search tdd` |
| 了解品質閘門 | `./scripts/get-config.sh --show shared/quality/gates.yaml` |
| 查看 Skill 清單 | `./scripts/get-config.sh --category skill-config` |
| 分析配置依賴 | `./scripts/get-config.sh --relations` |

## 擴充指南

### 添加新配置到索引

1. **確定分類**：選擇適當的 `type`（參考上方分類表）

2. **新增條目**：在 `entries:` 區段添加新條目

```yaml
entries:
  # ... 既有條目 ...

  - path: shared/config/new-config.yaml
    type: coordination-config
    description: "新配置的簡短說明"
    keys:
      - version: "1.0"
      - key_feature: value
    references:
      - shared/config/related-config.yaml
```

3. **更新分類計數**：增加對應 `categories[].count`

4. **驗證索引**：執行 `./scripts/get-config.sh --show shared/config/new-config.yaml`

### 命名規範

| 項目 | 規範 | 範例 |
|------|------|------|
| 配置檔名 | 小寫、kebab-case | `model-routing.yaml` |
| 分類 ID | 小寫、kebab-case、`-config` 後綴 | `skill-config` |
| 版本 | Semantic Versioning | `1.0.0`、`2.1.0` |
| 路徑 | 相對於專案根目錄 | `shared/config/xxx.yaml` |

### 分類標準

選擇分類時考慮：

- **skill-config**: 定義 Skill 行為的配置（SKILL.md）
- **perspective-config**: 定義視角、角色的配置
- **quality-config**: 控制品質、驗證、評分的配置
- **coordination-config**: 控制執行流程、並行、傳遞的配置
- **integration-config**: 外部服務、工具整合的配置
- **metrics-config**: 指標定義和收集的配置
- **schema-config**: 資料結構 Schema 定義
- **expertise-config**: 專業知識框架
- **plugin-config**: Plugin 本身的配置

## 配置關係

### 核心配置依賴圖

```
orchestrate/SKILL.md
    ├── execution-profiles.yaml ──→ model-routing.yaml
    ├── parallel-execution.yaml
    ├── early-termination.yaml
    ├── context-freshness.yaml
    └── gates.yaml ──→ scoring.yaml
                   └── rollback-strategy.yaml

research/SKILL.md, plan/SKILL.md, tasks/SKILL.md, ...
    ├── model-routing.yaml
    ├── gates.yaml
    └── [skill-specific configs]

catalog.yaml
    └── expertise-frameworks/*.yaml
```

### 配置載入順序

1. **Plugin 配置** (`plugin.json`) - 專案元資料
2. **執行模式** (`execution-profiles.yaml`) - 決定整體策略
3. **模型路由** (`model-routing.yaml`) - 模型選擇規則
4. **品質閘門** (`gates.yaml`) - 各階段通過標準
5. **Skill 配置** (`*/SKILL.md`) - 階段特定配置
6. **視角配置** (`catalog.yaml`) - 視角組合

### 主要配置間的依賴

| 配置 | 依賴 | 被依賴 |
|------|------|--------|
| `model-routing.yaml` | - | execution-profiles, 所有 Skill |
| `gates.yaml` | scoring.yaml | 所有 Skill |
| `execution-profiles.yaml` | model-routing.yaml | orchestrate |
| `parallel-execution.yaml` | - | orchestrate, implement |
| `catalog.yaml` | expertise-frameworks/* | 所有階段 Skill |

## 常見任務

### 查找特定功能的配置

```bash
# TDD 相關
./scripts/get-config.sh --search tdd

# 安全相關
./scripts/get-config.sh --search security

# 並行執行相關
./scripts/get-config.sh --search parallel
```

### 了解配置用途

```bash
# 查看詳細說明
./scripts/get-config.sh --show shared/config/context-freshness.yaml

# 查看關鍵欄位
yq '.entries[] | select(.path == "shared/config/context-freshness.yaml") | .keys' shared/config/INDEX.yaml
```

### 追蹤配置變更影響

```bash
# 查看哪些配置引用了特定配置
./scripts/get-config.sh --relations | grep "model-routing.yaml"
```

## 相關文檔

| 文檔 | 路徑 |
|------|------|
| 專案總覽 | [CLAUDE.md](../../CLAUDE.md) |
| 品質配置 | [shared/quality/](../quality/) |
| 視角配置 | [shared/perspectives/](../perspectives/) |
| 協調機制 | [shared/coordination/](../coordination/) |
