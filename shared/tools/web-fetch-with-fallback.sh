#!/bin/bash
# =============================================================================
# web-fetch-with-fallback.sh - WebFetch + Chrome Fallback
#
# 位置: shared/tools/web-fetch-with-fallback.sh
# 用途: 提供 WebFetch 失敗時的 Chrome fallback 策略指引
#
# 注意: 此腳本主要作為文檔，實際 fallback 由 Claude Agent 執行
# =============================================================================

cat << 'EOF'
# WebFetch Fallback 策略

當 WebFetch 失敗時，使用 Chrome 工具作為 fallback。

## 失敗原因

WebFetch 可能因以下原因失敗：
- 網站阻擋爬蟲 (403/429)
- 需要 JavaScript 渲染
- 需要登入/認證
- Rate limit
- 網路錯誤

## Fallback 流程

```
1. 先嘗試 WebFetch
   WebFetch { url: "...", prompt: "..." }
   ↓
2. 檢查結果
   ├── 成功 → 使用結果
   └── 失敗 → 進入 Chrome fallback
       ↓
3. Chrome Fallback
   a. mcp__claude-in-chrome__tabs_create_mcp → 建立新分頁
   b. mcp__claude-in-chrome__navigate { url: "..." } → 開啟 URL
   c. 等待頁面載入（約 2-3 秒）
   d. mcp__claude-in-chrome__get_page_text → 讀取內容
```

## Agent Prompt 範例

```markdown
### 網頁抓取策略

當需要抓取網頁時，請使用以下順序：

1. **優先使用 WebFetch**
   - 快速、輕量
   - 適合靜態網頁

2. **如果 WebFetch 失敗**，使用 Chrome：
   ```
   a. mcp__claude-in-chrome__tabs_create_mcp → 建立新分頁
   b. mcp__claude-in-chrome__navigate → 導航到 URL
   c. 等待頁面載入
   d. mcp__claude-in-chrome__get_page_text → 讀取內容
   ```

3. **如果仍然失敗**，記錄 URL 供人工處理
```

## 可用的 Chrome 工具

```
mcp__claude-in-chrome__navigate     - 導航到 URL
mcp__claude-in-chrome__read_page    - 讀取頁面內容（含結構）
mcp__claude-in-chrome__get_page_text - 獲取純文字
mcp__claude-in-chrome__tabs_create_mcp - 建立新分頁
mcp__claude-in-chrome__tabs_context_mcp - 獲取當前分頁資訊
```

## 注意事項

1. Chrome 工具需要 Claude in Chrome 擴展已安裝並運行
2. 某些網站可能仍需要手動登入
3. 避免過度使用 Chrome，會較慢且消耗更多資源
4. 記錄所有 fallback 事件到 logs/actions.jsonl

## Log 格式

```jsonl
{"timestamp": "...", "action": "web_fetch", "url": "...", "method": "WebFetch", "success": true}
{"timestamp": "...", "action": "web_fetch", "url": "...", "method": "WebFetch", "success": false, "error": "blocked"}
{"timestamp": "...", "action": "web_fetch_fallback", "url": "...", "method": "Chrome", "success": true}
```
EOF
