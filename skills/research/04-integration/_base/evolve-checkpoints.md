# Evolve Checkpoints Integration

> 與 evolve Skill 的 Checkpoint 機制整合

## Checkpoint 對應

Multi-Agent Research 的執行流程與 evolve Checkpoint 的對應關係：

| 研究階段 | evolve Checkpoint | 動作 |
|----------|-------------------|------|
| Phase 0: 北極星錨定 | CP0 | 設定研究目標和成功標準 |
| Phase 1: Memory 搜尋 | CP1 | 搜尋 .claude/memory/ 避免重複研究 |
| Phase 5: 匯總完成 | CP3 | 確認研究目標達成 |
| Phase 6: Memory 存檔 | CP3.5 | 同步 index.md |

## CP0: 北極星錨定

### 時機

研究開始前

### 動作

```markdown
## 北極星：{研究主題}

### 研究目標
- 主要問題：{核心問題}
- 期望輸出：{報告類型}

### 成功標準
- [ ] 回答了核心問題
- [ ] 多視角驗證
- [ ] 可行的行動建議

### 研究範圍
- 包含：{範圍內項目}
- 排除：{範圍外項目}
```

### 輸出

北極星錨定文件，用於後續驗證

## CP1: Memory 搜尋

### 時機

視角分解前

### 動作

```bash
# 搜尋相關研究
ls .claude/memory/research/

# 搜尋關鍵字
grep -r "{topic}" .claude/memory/
```

### 發現相關研究時

```
> 發現相關研究：
>   1. ai-agent-patterns (2025-01-15)
>   2. multi-agent-coordination (2025-01-10)
>
> 選項：
>   1. 復用並補充新發現
>   2. 從頭開始新研究
>   3. 取消
```

### 輸出

- 無相關研究：繼續
- 有相關研究：用戶決定是否復用

## CP3: 目標確認

### 時機

Reduce Phase 完成後

### 動作

對照北極星檢查：

```markdown
## 研究完成度檢查

### 對照北極星
- [x] 回答了核心問題
- [x] 4 視角完成研究
- [x] 交叉驗證完成
- [ ] 所有矛盾已解決（3 個未解決）

### 評估
研究基本完成，有 3 個矛盾標記為「需進一步研究」

### 決策
- 繼續：存檔並結束
- 深化：針對未解決矛盾進行額外研究
```

### 輸出

- 目標達成：進入存檔
- 目標未達：決定是否深化

## CP3.5: Memory 存檔

### 時機

研究完成，準備存檔

### 動作

1. 建立研究目錄
2. 存儲所有報告
3. 更新 index.md

### 目錄結構

```
.claude/memory/research/[topic-id]/
├── meta.yaml
├── overview.md
├── perspectives/
│   ├── architecture.md
│   ├── cognitive.md
│   ├── workflow.md
│   └── industry.md
└── synthesis.md
```

### 更新 index.md

```markdown
## research/

| ID | 主題 | 日期 | 視角數 |
|----|------|------|--------|
| ai-agent-architecture | AI Agent 架構設計 | 2025-01-21 | 4 |
```

### 驗證

```bash
# 確認文件存在
ls .claude/memory/research/[topic-id]/

# 確認 index 已更新
grep "[topic-id]" .claude/memory/index.md
```

## Checkpoint 執行清單

### 完整流程清單

```markdown
## Multi-Agent Research Checkpoint 清單

### CP0: 北極星錨定
- [ ] 定義研究目標
- [ ] 設定成功標準
- [ ] 確定研究範圍

### CP1: Memory 搜尋
- [ ] 搜尋 .claude/memory/research/
- [ ] 處理相關研究（如有）

### [執行研究]

### CP3: 目標確認
- [ ] 對照北極星驗證
- [ ] 評估完成度
- [ ] 決定是否深化

### CP3.5: Memory 存檔
- [ ] 建立目錄結構
- [ ] 存儲所有報告
- [ ] 更新 index.md
- [ ] 驗證存檔完整
```

## 與 evolve 的協作

### 當 evolve 呼叫 multi-research

```
evolve 執行任務
    ↓
需要深度研究
    ↓
呼叫 /multi-research
    ↓
multi-research 執行（遵循自己的 Checkpoint）
    ↓
返回研究結果
    ↓
evolve 繼續任務
```

### 研究結果傳遞

```markdown
## 研究完成

### 快速摘要
{一段話摘要}

### 關鍵發現
1. {發現 1}
2. {發現 2}
3. {發現 3}

### 詳細報告位置
.claude/memory/research/[topic-id]/synthesis.md

### 行動建議
1. {建議 1}
2. {建議 2}
```

## 錯誤處理

### Checkpoint 失敗

| Checkpoint | 可能原因 | 處理 |
|------------|---------|------|
| CP1 | Memory 目錄不存在 | 自動建立 |
| CP3 | 目標未完全達成 | 詢問是否繼續 |
| CP3.5 | 寫入失敗 | 重試或警告 |

### 降級處理

如果 Checkpoint 機制不可用（例如不在 evolve 環境中）：
- 跳過 evolve 特定檢查
- 仍執行核心研究流程
- Memory 存檔仍然執行
