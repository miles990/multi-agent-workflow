# Memory System Integration

> 研究結果的持久化存儲與檢索

## 目錄結構

```
.claude/memory/research/
├── index.md                      # 研究索引
└── [topic-id]/                   # 單一研究
    ├── meta.yaml                 # 元數據
    ├── overview.md               # 一頁概述
    ├── perspectives/             # 視角報告
    │   ├── architecture.md
    │   ├── cognitive.md
    │   ├── workflow.md
    │   └── industry.md
    └── synthesis.md              # 匯總報告
```

## 文件格式

### meta.yaml

```yaml
# 研究元數據
topic: AI Agent 架構設計模式
topic_id: ai-agent-architecture
date: 2025-01-21
duration: 45min

research_config:
  mode: normal           # quick | normal | deep
  perspectives:
    - architecture
    - cognitive
    - workflow
    - industry

results:
  consensus_count: 12
  conflict_count: 3
  resolved_count: 1
  unique_insights: 5

status: completed        # in_progress | completed | partial
```

### overview.md

```markdown
# {主題} - 研究概述

> 一頁摘要，快速了解研究結論

## 核心結論

{2-3 句話總結最重要的發現}

## 關鍵數據

| 指標 | 值 |
|------|-----|
| 視角數 | 4 |
| 共識點 | 12 |
| 矛盾點 | 3 (1 已解決) |

## 行動建議 TOP 3

1. {最重要的建議}
2. {第二重要的建議}
3. {第三重要的建議}

## 詳細資料

- [完整報告](./synthesis.md)
- [架構視角](./perspectives/architecture.md)
- [認知視角](./perspectives/cognitive.md)
```

### perspectives/{視角}.md

```markdown
# {視角名稱} 視角報告

## 研究者
{視角角色描述}

## 研究方法
{deep | search}

## 核心發現

### 發現 1: {標題}
{詳細描述}

**支持證據**：
- ...

**信心度**：高/中/低

### 發現 2: {標題}
...

## 建議

1. {建議 1}
2. {建議 2}

## 相關資源

- {資源 1}
- {資源 2}
```

### synthesis.md

```markdown
# {主題} - 匯總研究報告

## 摘要

{一段話總結}

## 研究配置

| 項目 | 值 |
|------|-----|
| 日期 | {date} |
| 模式 | {mode} |
| 視角 | {perspectives} |
| 時長 | {duration} |

## 共識發現

### 強共識 (多視角同意)

#### 1. {發現標題}
- **支持視角**：架構、認知、工作流、業界
- **內容**：{描述}
- **信心度**：★★★★

#### 2. {發現標題}
...

### 弱共識 (部分視角同意)
...

## 矛盾分析

### 已解決

#### 矛盾 1: {標題}
- **衝突視角**：{A} vs {B}
- **解決方案**：{方案}
- **決策依據**：{理由}

### 需進一步研究

#### 矛盾 2: {標題}
- **衝突視角**：{A} vs {B}
- **建議行動**：{下一步}

## 獨特洞察

來自單一視角的有價值發現：

1. **{視角}**：{洞察內容}
2. ...

## 關鍵洞察

整合所有視角後的深層發現：

1. {洞察 1}
2. {洞察 2}

## 行動建議

### 立即行動
- {行動 1}
- {行動 2}

### 短期規劃 (1-4 週)
- {規劃 1}

### 長期考量
- {考量 1}

## 附錄

### 視角報告連結
- [架構分析](./perspectives/architecture.md)
- [認知研究](./perspectives/cognitive.md)
- [工作流設計](./perspectives/workflow.md)
- [業界實踐](./perspectives/industry.md)
```

## 索引管理

### index.md 格式

```markdown
# Research Memory Index

> 所有研究記錄的索引

## 研究列表

| ID | 主題 | 日期 | 視角 | 狀態 |
|----|------|------|------|------|
| ai-agent-architecture | AI Agent 架構設計 | 2025-01-21 | 4 | completed |
| microservices-patterns | 微服務設計模式 | 2025-01-18 | 4 | completed |
| react-performance | React 效能優化 | 2025-01-15 | 3 | partial |

## 按主題分類

### 架構
- [ai-agent-architecture](./ai-agent-architecture/synthesis.md)
- [microservices-patterns](./microservices-patterns/synthesis.md)

### 前端
- [react-performance](./react-performance/synthesis.md)

## 最近研究

1. ai-agent-architecture (2025-01-21)
2. microservices-patterns (2025-01-18)
3. react-performance (2025-01-15)
```

### 索引更新規則

每次研究完成後：
1. 在「研究列表」表格中添加新行
2. 在對應的「按主題分類」下添加連結
3. 更新「最近研究」列表

## 搜尋與檢索

### 搜尋相關研究

```bash
# 關鍵字搜尋
grep -r "微服務" .claude/memory/research/

# 按日期範圍
find .claude/memory/research/ -name "meta.yaml" -exec grep -l "date: 2025-01" {} \;

# 按狀態
grep -l "status: completed" .claude/memory/research/*/meta.yaml
```

### 復用研究

當找到相關研究時：

```markdown
## 發現相關研究

### 相關研究
- ID: {topic-id}
- 主題: {topic}
- 日期: {date}
- 相關度: 高/中/低

### 選項
1. **復用並補充**：基於現有研究，補充新視角
2. **完全重做**：忽略舊研究，從頭開始
3. **取消**：不執行新研究
```

## 清理與維護

### 過期研究處理

建議保留期限：
- 技術選型研究：6 個月
- 架構設計研究：1 年
- 方法論研究：永久

### 清理流程

```bash
# 列出超過 6 個月的研究
find .claude/memory/research/ -name "meta.yaml" -mtime +180

# 手動決定是否歸檔或刪除
```

### 歸檔格式

```
.claude/memory/archive/research/
└── 2024/
    └── {topic-id}/
```
