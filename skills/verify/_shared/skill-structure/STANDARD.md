# Skill Standard Structure

> Claude Code Plugin 標準 Skill 結構規範 v1.0.0

## 總覽

本規範定義了 Claude Code Plugin 的標準 Skill 結構，確保一致性、可維護性和自動化整合。

## 目錄結構

### 必須檔案

```
skills/{skill-name}/
├── SKILL.md                    # Skill 主檔案（frontmatter + 說明）
├── 00-quickstart/              # 快速開始目錄
│   └── _base/
│       └── usage.md            # 使用指南
└── 01-perspectives/            # 視角定義目錄
    └── _base/
        ├── default-perspectives.md   # 預設視角
        └── custom-perspectives.md    # 自訂視角指南（可選）
```

### 建議檔案

```
skills/{skill-name}/
├── config/                     # 配置檔案目錄
│   ├── phases.yaml             # 執行階段配置
│   └── quality-gates.yaml      # 品質閘門配置
└── templates/                  # 模板檔案目錄
    ├── meta.yaml.template      # 元數據模板
    └── summary.md.template     # 摘要模板
```

### 可選檔案

```
skills/{skill-name}/
├── examples/                   # 範例檔案
│   └── basic-usage.md
└── tests/                      # 測試相關
    └── test-cases.yaml
```

## SKILL.md 規範

### Frontmatter 必要欄位

```yaml
---
name: skill-name                # Skill 名稱（小寫、連字號）
version: X.Y.Z                  # 語義化版本
description: 簡短描述           # 一句話說明
triggers: [trigger1, trigger2]  # 觸發關鍵字
context: fork|shared            # Context 類型
agent: agent-type               # 預設 Agent 類型
allowed-tools: [Read, Write]    # 允許使用的工具
model: sonnet|haiku|opus        # 預設模型
---
```

### Frontmatter 可選欄位

```yaml
---
requires: [other-skill]         # 依賴的其他 Skills
inputs: [input-type]            # 預期輸入類型
outputs: [output-type]          # 產出類型
stage: RESEARCH|PLAN|...        # 工作流階段
hooks: true|false               # 是否使用 Claude Code Hooks
---
```

### 標準段落

#### 1. 標題與簡介

```markdown
# {Skill Name} v{X.Y.Z}

> 簡短的一句話描述，說明核心價值
```

#### 2. 自動化機制（如有使用 hooks）

```markdown
## 自動化機制

> ⚡ **本 skill 已整合 Claude Code Hooks**
>
> - Action logging、state tracking、git commit 均由 hooks 自動處理
> - 只需執行 CP1 初始化，其餘檢查點自動執行
```

#### 3. 使用方式

```markdown
## 使用方式

```bash
/command [參數]
/command 具體範例
```

**Flags**: `--flag1` | `--flag2` | `--flag3`
```

#### 4. 角色配置（多 Agent 模式）

```markdown
## 角色配置

| ID | 名稱 | 模型 | 聚焦 |
|----|------|------|------|
| `agent-id` | 角色名稱 | sonnet | 職責說明 |

→ 模型路由配置：[shared/config/model-routing.yaml](../../shared/config/model-routing.yaml)
```

#### 5. 執行流程

```markdown
## 執行流程

```
CP1: 工作流初始化 ⚡ 手動執行
    python scripts/hooks/init_workflow.py --topic "{topic}" --stage {STAGE}
    ↓
Phase 0: 階段說明
    ↓
Phase 1: 階段說明
    ↓
...
    ↓
CP4: Task Commit ✅ 自動執行
    [寫入 .claude/memory/ 時自動 git commit]
```
```

#### 6. 關鍵機制（如 TDD、品質閘門、早期錯誤攔截等）

```markdown
## {機制名稱}

說明機制的運作方式和重要性

→ 配置：[shared/xxx/xxx.yaml](../../shared/xxx/xxx.yaml)
```

#### 7. CP4: Task Commit

```markdown
## CP4: Task Commit

**每個 {單位} 完成後**必須執行 CP4 Task Commit。

```
Phase X: 階段名稱
    ↓
CP4: Task Commit（每個 {單位}）
    ├── git add {files}
    └── git commit -m "type(scope): message"
```

→ 協議：[shared/git/commit-protocol.md](../../shared/git/commit-protocol.md)
```

#### 8. 品質閘門

```markdown
## 品質閘門

通過條件（{STAGE} 階段）：
- ✅ 條件 1
- ✅ 條件 2
- ✅ 品質分數 ≥ XX

→ 閘門配置：[shared/quality/gates.yaml](../../shared/quality/gates.yaml)
```

#### 9. 輸出結構

```markdown
## 輸出結構

```
.claude/memory/{type}/[id]/
├── meta.yaml               # 元數據
├── perspectives/           # 完整報告（MAP 產出，保留）
│   └── ...
├── summaries/              # 結構化摘要（REDUCE 產出，供快速查閱）
│   └── ...
└── summary.md              # 主輸出
```

> ⚠️ 說明各目錄用途
```

#### 10. Agent 能力限制（多 Agent 模式）

```markdown
## Agent 能力限制

**子 Agent 不應該開啟 Task**：

| 允許的操作 | 說明 |
|-----------|------|
| ✅ Read | 讀取檔案 |
| ✅ Write | 寫入報告 |
| ❌ Task | 開子 Agent |
```

#### 11. 行動日誌

```markdown
## 行動日誌

每個工具調用完成後，記錄到 `.claude/workflow/{workflow-id}/logs/actions.jsonl`。

**記錄時機**：
- 成功：記錄 `tool`、`input`、`output_preview`、`duration_ms`、`status: success`
- 失敗：記錄 `tool`、`input`、`error`、`stderr`（如有）、`status: failed`

**關鍵行動（{STAGE} 階段）**：
| 行動 | 記錄重點 |
|------|----------|
| Read | `file_path`、`output_size` |
| Write | `file_path`、`content_size` |

**排查問題**：
```bash
# 查看階段失敗行動
jq 'select(.stage == "{STAGE}" and .status == "failed")' actions.jsonl
```

→ 日誌規範：[shared/communication/execution-logs.md](../../shared/communication/execution-logs.md)
```

#### 12. 共用模組

```markdown
## 共用模組

| 模組 | 用途 |
|------|------|
| [module](../../shared/path/to/module) | 說明 |
```

#### 13. 工作流位置

```markdown
## 工作流位置

```
RESEARCH → PLAN → TASKS → IMPLEMENT → REVIEW → VERIFY
             ↑
          你在這裡
```

- **輸入**：來自上游 skill
- **輸出**：提供給下游 skill
```

## 00-quickstart 規範

### 目錄結構

```
00-quickstart/
└── _base/
    └── usage.md        # 使用指南
```

### usage.md 必要段落

1. **標題與簡介**
   ```markdown
   # Quick Start Guide

   > 3 分鐘快速上手 {Skill Name}
   ```

2. **最簡用法**
   ```markdown
   ## 最簡用法

   ```bash
   /command 簡單範例
   ```

   這會：
   1. 步驟 1
   2. 步驟 2
   3. ...
   ```

3. **常用模式**
   ```markdown
   ## 常用模式

   ### 模式 1

   ```bash
   /command --flag 範例
   ```

   適用：使用場景
   ```

4. **輸出位置**
   ```markdown
   ## 輸出位置

   所有結果存儲在：

   ```
   .claude/memory/{type}/[id]/
   └── ...
   ```
   ```

5. **下一步**
   ```markdown
   ## 下一步

   - [了解視角](../../01-perspectives/_base/default-perspectives.md)
   - [進階配置](../../config/xxx.yaml)
   ```

## 01-perspectives 規範

### 目錄結構

```
01-perspectives/
└── _base/
    ├── default-perspectives.md     # 預設視角
    └── custom-perspectives.md      # 自訂視角指南（可選）
```

### default-perspectives.md 必要段落

1. **標題與簡介**
   ```markdown
   # Default Perspectives

   > 預設視角配置：說明
   ```

2. **視角總覽**（視覺圖）
   ```markdown
   ## 視角總覽

   ```
   ASCII 圖表
   ```
   ```

3. **每個視角的詳細說明**
   ```markdown
   ## 視角 X: {名稱} ({id})

   ### 角色定位

   簡短說明

   ### 規劃重點

   - 重點 1
   - 重點 2

   ### Prompt 模板

   ```
   實際的 prompt 範本
   ```
   ```

4. **視角組合策略**
   ```markdown
   ## 視角組合策略

   ### 場景 1

   推薦：視角 A + 視角 B
   - 理由
   ```

## 錯誤處理標準

### SKILL.md 中的錯誤處理段落

```markdown
## 錯誤處理

### 常見錯誤

#### 錯誤 1: 說明

**症狀**：
- 現象描述

**原因**：
- 根本原因

**解決方案**：
```bash
# 解決步驟
```

### 故障排除

1. 檢查項目 1
2. 檢查項目 2

→ 完整故障排除：[shared/errors/troubleshooting.md](../../shared/errors/troubleshooting.md)
```

## 配置檔案標準

### phases.yaml

```yaml
# 執行階段配置
phases:
  - id: phase-0
    name: 階段名稱
    required: true
    timeout: 300

  - id: phase-1
    name: 階段名稱
    depends_on: [phase-0]
    parallel: true
```

### quality-gates.yaml

```yaml
# 品質閘門配置
stage: STAGE_NAME
minimum_score: 70

criteria:
  - id: criterion-1
    name: 標準名稱
    weight: 0.3
    threshold: 0.8
```

## 模板檔案標準

### meta.yaml.template

```yaml
# Skill 元數據模板
skill: {{skill_name}}
version: {{skill_version}}
workflow_id: {{workflow_id}}
stage: {{stage}}
started_at: {{timestamp}}
completed_at: null
status: in_progress

input:
  # 輸入參數

output:
  # 輸出檔案路徑
```

### summary.md.template

```markdown
# {{skill_name}} Summary

> 執行時間：{{started_at}} - {{completed_at}}

## 概要

簡短摘要

## 關鍵產出

- 產出 1
- 產出 2

## 品質指標

| 指標 | 分數 | 狀態 |
|------|------|------|
| 指標1 | {{score}} | {{status}} |

## 下一步

建議的後續行動
```

## 檔案命名規範

### 目錄命名

- 使用小寫、連字號：`skill-name`
- 編號前綴使用兩位數：`00-quickstart`、`01-perspectives`

### 檔案命名

- Markdown 檔案：小寫、連字號：`default-perspectives.md`
- YAML 檔案：小寫、連字號：`quality-gates.yaml`
- 模板檔案：`.template` 後綴：`meta.yaml.template`

### 特殊目錄

- `_base/`：基礎/預設內容目錄
- `config/`：配置檔案
- `templates/`：模板檔案
- `examples/`：範例檔案
- `tests/`：測試檔案

## 文檔風格

### Markdown 標題

- H1 (`#`)：主標題（每個檔案一個）
- H2 (`##`)：主要段落
- H3 (`###`)：子段落
- H4 (`####`)：詳細項目

### 表格

- 保持對齊
- 使用清晰的欄位名稱
- 提供說明欄位

### 程式碼區塊

- 明確指定語言：` ```bash `、` ```yaml `
- 包含註解說明
- 提供完整範例

### 連結

- 相對路徑：`[text](../../shared/path/to/file.md)`
- 使用箭頭指向：`→ 配置：[link](path)`

### 視覺元素

- 使用 ASCII 圖表
- 使用表格呈現結構化資訊
- 使用 emoji 標記重要資訊：⚡ ✅ ❌ ⚠️

### 引用區塊

```markdown
> 重要提示或簡介
```

## 版本控制

### 語義化版本

- `X.Y.Z` 格式
- X：重大變更（breaking changes）
- Y：新功能（backward compatible）
- Z：Bug 修復（backward compatible）

### 變更記錄

在 SKILL.md 底部可選添加：

```markdown
## 變更記錄

### v3.0.0 (2025-01-27)
- 重大變更說明

### v2.1.0 (2025-01-20)
- 新功能說明
```

## 整合規範

### Claude Code Hooks

如 Skill 使用 hooks：

1. 在 frontmatter 標記：`hooks: true`
2. 在「自動化機制」段落說明
3. 在「執行流程」中標記自動執行的檢查點
4. 在「CP4: Task Commit」中說明自動化行為

### 共用模組引用

- 使用相對路徑：`../../shared/`
- 使用箭頭格式：`→ 配置：[link](path)`
- 保持連結有效性

### Memory 存檔

所有輸出應遵循：

```
.claude/memory/{type}/[id]/
├── meta.yaml           # 元數據（必須）
├── summary.md          # 摘要（必須）
├── perspectives/       # 視角報告（多 Agent）
└── summaries/          # 結構化摘要（多 Agent）
```

## 遵循原則

1. **一致性**：所有 Skills 使用相同結構
2. **完整性**：必須檔案都存在
3. **清晰性**：說明簡潔明確
4. **可維護性**：易於更新和擴展
5. **自動化**：支援工具自動處理
6. **可發現性**：易於搜尋和理解

## 檢查清單

建立新 Skill 時，確認：

- [ ] SKILL.md 包含所有必要段落
- [ ] Frontmatter 包含所有必要欄位
- [ ] 00-quickstart/\_base/usage.md 存在
- [ ] 01-perspectives/\_base/default-perspectives.md 存在（多 Agent）
- [ ] 所有連結有效
- [ ] 版本號正確
- [ ] 配置檔案完整（如需要）
- [ ] 模板檔案提供（如需要）
- [ ] 錯誤處理說明完整
- [ ] 遵循檔案命名規範

## 參考範例

完整範例參考：
- [skills/research/](../../skills/research/)
- [skills/plan/](../../skills/plan/)
- [skills/implement/](../../skills/implement/)
