# Memory System Integration（共用模組）

> 工作成果的持久化存儲與檢索

## 概述

所有 skill 的輸出都存儲在 `.claude/memory/` 下，按 skill 類型分類。

**此為共用模組**，定義統一的 Memory 結構和操作規範。

## 目錄結構

```
.claude/memory/
├── index.md                      # 全域索引
├── research/                     # research skill 產出
│   ├── index.md                  # research 索引
│   └── [topic-id]/
├── plans/                        # plan skill 產出
│   ├── index.md
│   └── [feature-id]/
├── implementations/              # implement skill 產出
│   ├── index.md
│   └── [feature-id]/
├── reviews/                      # review skill 產出
│   ├── index.md
│   └── [review-id]/
└── verifications/                # verify skill 產出
    ├── index.md
    └── [feature-id]/
```

## 單一記錄結構（統一目錄）

每個記錄目錄的標準結構：

```
[record-id]/
├── meta.yaml                 # 元數據（workflow 資訊）
├── overview.md               # 一頁概述
├── perspectives/             # 完整視角報告（Map Phase 產出）
│   ├── {perspective-1}.md    #   完整分析內容
│   ├── {perspective-2}.md
│   └── ...
├── summaries/                # 結構化摘要（Reduce Phase 產出）
│   ├── {perspective-1}.yaml  #   供快速查閱和交叉驗證
│   ├── {perspective-2}.yaml
│   └── ...
├── {primary-output}.md       # 主輸出（因 skill 而異）
├── metrics.yaml              # 執行指標
└── logs/                     # 日誌（也在這裡！）
    ├── events.jsonl          # 事件日誌（所有工具調用）
    ├── actions.jsonl         # 行動日誌（詳細參數）
    └── errors.jsonl          # 錯誤日誌（失敗的操作）
```

> **注意**：`perspectives/` 保存完整報告，`summaries/` 保存結構化摘要。
> 兩者都必須保留，完整報告用於追溯，摘要用於快速查閱。
>
> **重要改進**：`logs/` 目錄也放在 memory 下，確保所有相關資料都在同一位置。

### 日誌檔案說明

| 檔案 | 用途 | 寫入來源 |
|------|------|----------|
| `events.jsonl` | 所有工具調用記錄 | Hook 自動記錄 |
| `actions.jsonl` | 應用層事件記錄 | CLI 主動記錄 |
| `errors.jsonl` | 失敗的操作記錄 | Hook 自動記錄 |

### 查詢日誌範例

```bash
# 查看執行流程
jq -s '.' logs/actions.jsonl

# 查看底層工具調用
jq 'select(.tool_name == "Task")' logs/events.jsonl

# 查看所有錯誤
cat logs/errors.jsonl | jq .
```

### 主輸出對應

| Skill | 主輸出檔案 |
|-------|------------|
| research | synthesis.md |
| plan | implementation-plan.md |
| implement | implementation-log.md |
| review | review-summary.md |
| verify | release-decision.md |

## 文件格式

### meta.yaml

```yaml
# 通用元數據格式
id: string                    # 記錄 ID
topic: string                 # 主題/功能名稱
skill: string                 # 產出 skill（research/plan/implement/review/verify）
date: YYYY-MM-DD
duration: string              # 執行時長（如 45min）

config:
  mode: quick | normal | deep
  perspectives: [list]

results:
  # skill 專屬結果摘要

status: in_progress | completed | partial

# 可選：關聯記錄
related:
  research: [record-id]       # 相關研究
  plan: [record-id]           # 相關計劃
  implementation: [record-id] # 相關實作
```

### overview.md

```markdown
# {主題} - 概述

> 一頁摘要，快速了解核心結論

## 核心結論

{2-3 句話總結最重要的發現}

## 關鍵數據

| 指標 | 值 |
|------|-----|
| 視角數 | N |
| {skill 專屬指標} | ... |

## 行動建議 TOP 3

1. {最重要的建議}
2. {第二重要的建議}
3. {第三重要的建議}

## 詳細資料

- [完整報告](./{primary-output}.md)
- [視角 A](./perspectives/a.md)
```

### perspectives/{視角}.md

```markdown
# {視角名稱} 視角報告

## 角色
{角色描述}

## 研究/工作方法
{method}

## 核心發現

### 發現 1: {標題}
{詳細描述}

**支持證據**：
- ...

**信心度**：高/中/低

## 建議

1. {建議 1}
2. {建議 2}

## 風險/注意事項

- {風險 1}
```

## 索引管理

### 全域 index.md

```markdown
# Memory Index

> 所有記錄的索引

## 快速導航

- [research/](./research/index.md) - 研究記錄
- [plans/](./plans/index.md) - 規劃記錄
- [implementations/](./implementations/index.md) - 實作記錄
- [reviews/](./reviews/index.md) - 審查記錄
- [verifications/](./verifications/index.md) - 驗證記錄

## 最近記錄

| 類型 | ID | 主題 | 日期 |
|------|-----|------|------|
| research | ... | ... | ... |
| plan | ... | ... | ... |
```

### 分類 index.md

```markdown
# {Skill Type} Memory Index

## 記錄列表

| ID | 主題 | 日期 | 狀態 |
|----|------|------|------|
| {id} | {topic} | {date} | {status} |

## 按主題分類

### {分類 1}
- [{id}](./{id}/overview.md) - {topic}

### {分類 2}
- ...

## 最近記錄

1. {id} ({date})
2. ...
```

### 索引更新規則

每次記錄完成後：
1. 在分類 index.md 的「記錄列表」中添加新行
2. 在對應的「按主題分類」下添加連結
3. 更新「最近記錄」列表
4. 更新全域 index.md 的「最近記錄」

## 搜尋與檢索

### 搜尋相關記錄

```bash
# 關鍵字搜尋
grep -r "關鍵字" .claude/memory/

# 按日期範圍
find .claude/memory/ -name "meta.yaml" -exec grep -l "date: 2025-01" {} \;

# 按狀態
grep -l "status: completed" .claude/memory/**/meta.yaml

# 按 skill 類型
ls .claude/memory/{skill-type}/
```

### 復用記錄

當找到相關記錄時：

```markdown
## 發現相關記錄

### 記錄資訊
- ID: {record-id}
- 類型: {skill}
- 主題: {topic}
- 日期: {date}
- 相關度: 高/中/低

### 選項
1. **復用並補充**：基於現有記錄，補充新內容
2. **完全重做**：忽略舊記錄，從頭開始
3. **取消**：不執行
```

## 清理與維護

### 建議保留期限

| 記錄類型 | 建議保留期限 |
|----------|-------------|
| 技術選型研究 | 6 個月 |
| 架構設計 | 1 年 |
| 實作記錄 | 永久（作為歷史記錄） |
| 審查記錄 | 6 個月 |
| 驗證記錄 | 版本發布後可歸檔 |

### 歸檔格式

```
.claude/memory/archive/{skill-type}/
└── {year}/
    └── {record-id}/
```

## 配置參數

```yaml
memory:
  base_path: .claude/memory
  paths:
    research: research/
    plan: plans/
    implement: implementations/
    review: reviews/
    verify: verifications/
  index:
    auto_update: true
    max_recent: 10
  cleanup:
    enabled: false
    retention_days: 180
```

## 錯誤處理

| 錯誤 | 處理 |
|------|------|
| 目錄不存在 | 自動建立 |
| index.md 不存在 | 自動建立 |
| 寫入失敗 | 重試一次，仍失敗則警告 |
| 重複 ID | 添加時間戳後綴 |

## Worktree 模式的 Memory 處理

### 核心原則

在 Worktree 模式下，**Memory 始終存儲在 main 目錄中**：

```yaml
worktree_memory_principle:
  memory_location: "{main_directory}/.claude/memory"
  never: "{worktree_directory}/.claude/memory"

  rationale:
    - Memory 是單一事實來源
    - 避免 worktree 間的 Memory 衝突
    - 確保 Memory 不會隨 worktree 刪除而遺失
```

### 路徑解析

```yaml
path_resolution:
  in_worktree:
    # 檢測是否在 worktree 中
    detection: "git rev-parse --git-common-dir | grep -q '.git/worktrees'"

    # 解析 main 目錄
    main_directory: |
      git rev-parse --git-common-dir | sed 's|/.git/worktrees/.*||'

    # Memory 路徑
    memory_path: "{main_directory}/.claude/memory"

  in_main:
    memory_path: ".claude/memory"
```

### 實際命令

```bash
# 獲取 Memory 路徑（適用於任何環境）
get_memory_path() {
    local git_common=$(git rev-parse --git-common-dir 2>/dev/null)

    if [[ "$git_common" == *".git/worktrees"* ]]; then
        # 在 worktree 中，解析 main 目錄
        local main_dir=$(echo "$git_common" | sed 's|/.git/worktrees/.*||')
        echo "$main_dir/.claude/memory"
    else
        # 在 main 目錄中
        echo "$(git rev-parse --show-toplevel)/.claude/memory"
    fi
}
```

### workflow.yaml 追蹤

```yaml
# 在 Worktree 模式下的 workflow.yaml
workflow:
  id: "user-auth"

  paths:
    main_directory: "/project"
    worktree_directory: "/project/.worktrees/user-auth"
    memory_base: "/project/.claude/memory"  # 始終指向 main

  worktree:
    enabled: true
    state: "active"
```

詳見：[../isolation/path-resolution.md](../isolation/path-resolution.md)
