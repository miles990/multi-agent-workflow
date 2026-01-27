# 業界實踐專家 報告

**視角 ID**: industry
**執行時間**: 2026-01-27
**主題**: Clawdbot 組件化 - 業界最佳實踐視角

## 核心發現

### 1. 現有組件化架構已具雛形

Clawdbot 已通過 `extensions/` 目錄和 `plugin-sdk` 實現初步的模組化。但源碼（`src/telegram`, `src/discord` 等）仍與核心耦合，未完全獨立發布為 npm 包。擴展包目前只是 pnpm workspace 中的同級模組，缺乏真正的包邊界定義。

### 2. Channel Plugin 契約設計良好，但文檔不足

ChannelPlugin 類型系統（72 個導出的 Channel* 類型）定義了明確的介面契約。但實作檔案需要進一步分離關注點，使第三方實現者更容易上手。

### 3. Monorepo 策略達到瓶頸

當前 pnpm workspace 設定（30+ extensions，每個都與主包共享 node_modules）造成：
- 版本同步困難（所有 packages 同時發佈）
- 依賴膨脹（每個擴展都暴露完整的主包依賴）
- 類型安全風險（擴展可能不正確使用內部 API）

### 4. 與業界成熟 SDK 的差距

對比 Telegram Bot API SDK、Discord.js、Slack Bolt 等：
- 成熟 SDK 都提供 "minimal core + pluggable features" 模式
- Clawdbot 的 Channel 概念本質上是 "multi-protocol adapter"
- 最佳實踐是將 protocol logic 與 orchestration logic 分離

## 詳細分析

### 現有模式評估

**積極方面**：
- Plugin System 使用工廠模式註冊（`registry.ts`），支援動態載入
- 清晰的適配器介面（`ChannelAuthAdapter`, `ChannelMessagingAdapter` 等）
- Extensions 已經實現了基本的隔離

**問題方面**：
- 70+ 千行代碼集中在 `src/channels/`
- 頻道邏輯仍要穿過全局配置系統
- 缺乏獨立測試環境

### 業界對標分析

| 專案 | 架構模式 | Clawdbot 可借鑒 |
|------|---------|---------------|
| Discord.js | Collection → Gateway → Client 分層 | 清晰的職責分離 |
| Telegram Bot API SDK | Builder pattern + Middleware | 構建器模式簡化配置 |
| Slack Bolt | Event-driven + Middleware chain | 事件驅動解耦 |
| Matrix SDK | Protocol 與 Client 完全分離 | Protocol 層獨立 |
| OpenAI SDK | `exports` 欄位做精細 API 邊界控制 | 精確的導出控制 |

### npm Package 最佳實踐比較

| 實踐 | 業界標準 | Clawdbot 現狀 | 建議 |
|------|---------|-------------|------|
| Peer Dependencies | 明確聲明 | 部分實現 | 全面使用 |
| 型別導出 | 完整 `.d.ts` | 良好 | 維持 |
| ESM + CJS | Dual build | 僅 ESM | 考慮兼容 |
| Exports 欄位 | 精確控制 | 基本使用 | 擴展 |
| Changelog | 自動化 | 手動 | 使用 Changesets |

### Monorepo vs Multi-repo 評估

**保持 Monorepo（推薦）**：
- 優勢：共享測試基礎設施、原子式重構、CI/CD 簡化
- 劣勢：版本管理複雜度，需要精心設計 package boundaries
- 工具建議：使用 Lerna + Changesets 或 Turborepo

**建議的 workspace 結構**：
```yaml
packages/
  core/              # @clawdbot/core
    src/plugin-sdk/
    src/config/types/
    package.json
  channels/
    telegram/        # @clawdbot/channel-telegram
    discord/         # @clawdbot/channel-discord
  extensions/        # 保持現狀，可選
```

## 最佳實踐建議

### Package 拆分路線圖

**第一層 - Core SDK（建議作為獨立 npm 包）**
```
@clawdbot/core
- plugin-sdk/types (ChannelPlugin, ChannelAuthAdapter 等)
- config/types (ClawdbotConfig 的核心類型)
- utils (normalizeAccountId, DEFAULT_ACCOUNT_ID 等)
- 需要遵循 semver，保持 API 穩定性
```

**第二層 - Protocol Implementations**
```
@clawdbot/channel-telegram
@clawdbot/channel-discord
@clawdbot/channel-slack
@clawdbot/channel-line

每個只依賴 @clawdbot/core，不依賴彼此
支援独立版本管理
```

**第三層 - Optional Extensions**
```
@clawdbot/memory-lancedb
@clawdbot/auth-google
@clawdbot/diagnostics-otel

Optional dependencies，基於 plugin-sdk only
```

### npm Package 配置建議

```json
{
  "name": "@clawdbot/channel-telegram",
  "version": "1.0.0",
  "type": "module",
  "exports": {
    ".": {
      "types": "./dist/index.d.ts",
      "import": "./dist/index.js"
    }
  },
  "peerDependencies": {
    "@clawdbot/core": "^1.0.0"
  },
  "peerDependenciesMeta": {
    "@clawdbot/core": { "optional": false }
  }
}
```

### 版本管理策略

| 策略 | 適用場景 | 建議 |
|------|---------|------|
| Fixed Versioning | 緊密耦合的 packages | @clawdbot/core + channels |
| Independent Versioning | 獨立的 extensions | @clawdbot/memory-* |
| Changesets | 自動化版本管理 | 全部使用 |

### CI/CD 最佳實踐

1. **獨立測試**：每個 package 有獨立的測試命令
2. **變更檢測**：只發布有變更的套件
3. **依賴圖感知**：按依賴順序發布
4. **預發布驗證**：在 npm publish 前驗證類型和 exports

## 實作路線圖

### 第 1 個月 - 基礎分層

- [ ] 將 plugin-sdk 遷出到獨立的 @clawdbot/core 包
- [ ] 提取 Channel 基礎類型到 core 中
- [ ] 為 @clawdbot/core 建立獨立的 CI/CD 管道
- [ ] 設定 Changesets 自動化版本管理

### 第 2 個月 - Channel 獨立化

- [ ] 將 src/telegram → packages/channels/telegram
- [ ] 將 src/discord → packages/channels/discord
- [ ] 配置獨立版本號
- [ ] 建立 channel package template

### 第 3 個月 - 發佈策略

- [ ] 在 npm 上發佈 @clawdbot/core@1.0.0
- [ ] 發佈 @clawdbot/channel-{protocol}@1.0.0
- [ ] 驗證第三方開發者能否單獨安裝
- [ ] 撰寫 Channel 開發指南

### 長期目標

- [ ] 建立 Plugin Marketplace
- [ ] 提供 SaaS 版本
- [ ] 開放 API 讓其他應用整合

## 關鍵風險與緩解

| 風險 | 緩解策略 |
|------|--------|
| 破壞現有用戶 | 長期維護舊 package.json exports，提供遷移指南 |
| 版本碎片化 | 使用 Changesets，自動化版本管理 |
| 類型安全 | 在 core 中強制使用 `as const` 和 branded types |
| 文檔漂移 | 為每個 Channel package 編寫獨立的 README，在 CI 中驗證 |

## 參考資料

- [Telegram Bot API 官方 SDK](https://github.com/telegraf/telegraf)：使用 "builder pattern" + "middleware system"
- [Discord.js](https://discord.js.org/)：清晰的 "Collection → Gateway → Client" 分層
- [Matrix SDK](https://github.com/matrix-org/matrix-js-sdk)：channel/room 與 protocol 的完全分離
- [OpenAI SDK](https://github.com/openai/openai-node)：使用 `exports` 欄位做精細的 API 邊界控制
- [Changesets](https://github.com/changesets/changesets)：Monorepo 版本管理最佳實踐

## 信心度

高 - 基於業界成熟專案對標分析

---
*由業界實踐專家視角產出*
