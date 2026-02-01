# 業界實踐研究員報告

> Plugin/Extension 開發的業界最佳實踐研究

**研究員**：業界實踐研究員
**日期**：2026-02-01
**版本**：1.0.0

## 核心發現

### 1. IDE Plugin 市場的進化方向

- **VS Code**：月度 API 發布，自動化市場部署成為標準
- **JetBrains**：統一簡化供應商邏輯，優化 CI/CD 整合
- **關鍵趨勢**：自動化簽名、GitHub Actions 工作流集成、版本一致性檢查

### 2. 自動化發布工具的三角戰爭

| 工具 | 特點 | 適用場景 |
|------|------|---------|
| **semantic-release** | 完全自動化，commit message 驅動 | 單包項目 |
| **changesets** | monorepo 友好，分離版本和 commit | 多包項目 |
| **release-please** | Google 出品，PR 驅動，審核友好 | 需審核的項目 |

### 3. Dogfooding 的現代實踐

- **TypeScript**：正在放棄自舉，改用 Go 重寫編譯器（10 倍性能）
- **Rust**：堅持自舉模式，但面臨複雜性挑戰
- **Lesson**：Dogfooding 有益但不是必須，性能收益可能超過工程複雜度

### 4. 版本一致性檢查的自動化

- Buf、openapi-diff 等工具可自動檢測破壞性變更
- 應在 CI/CD 中集成 API 兼容性檢查
- 版本碰撞應該自動偵測而非手動管理

### 5. 熱載入/監控開發工作流

- fswatch（macOS）、inotifywait（Linux）、polling（備選）已成標準
- Compose Hot Reload 1.0.0 剛發布，強調小型遞增更改優勢
- **增量同步（Hash-based）比全量同步快 20-100 倍**

## 詳細分析

### IDE Plugin 開發實踐

#### VS Code Extension

**工作流標準**：
```yaml
# .github/workflows/release.yml
on:
  push:
    tags: ['v*']

jobs:
  release:
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm test
      - run: npx vsce package
      - run: npx vsce publish
        env:
          VSCE_PAT: ${{ secrets.VSCE_PAT }}
```

**關鍵實踐**：
- 版本從 `package.json` 讀取
- Tag 觸發發布
- PAT (Personal Access Token) 管理市場權限
- 自動化測試必須通過

#### JetBrains Plugin

**2025-2026 更新**：
- 簡化供應商特定邏輯
- 改進 Gradle IntelliJ Plugin 整合
- 統一 UI 測試框架

**發布流程**：
```kotlin
// build.gradle.kts
intellijPlatform {
    publishing {
        token.set(providers.gradleProperty("intellijPublishToken"))
        channels.set(listOf("stable"))
    }
}
```

### CLI 工具開發實踐

#### npm/yarn Plugin 系統

**最佳實踐**：
- `package.json` 作為單一真相來源
- `npm version` + `npm publish` 簡化流程
- `prepublishOnly` hook 確保測試通過

**自動化範例**：
```json
{
  "scripts": {
    "prepublishOnly": "npm test && npm run build",
    "version": "npm run changelog && git add CHANGELOG.md",
    "postversion": "git push && git push --tags"
  }
}
```

#### Homebrew Tap 機制

**發布流程**：
1. 更新 Formula 檔案
2. 計算 SHA256
3. 提交到 tap 倉庫
4. Homebrew 自動同步

**自動化工具**：`brew bump-formula-pr`

### 自動化發布工具比較

#### semantic-release

**優點**：
- 完全自動化（零人工干預）
- Conventional Commits 驅動
- 豐富的插件生態

**缺點**：
- 學習曲線陡峭
- monorepo 支援較弱
- 難以人工介入

**適用**：單包項目、高頻發布

#### changesets

**優點**：
- monorepo 原生支援
- 版本與 commit 分離
- 團隊控制力強

**缺點**：
- 需要手動創建 changeset
- 額外的 `.changeset/` 目錄

**適用**：monorepo、團隊協作

#### release-please

**優點**：
- PR 驅動，審核友好
- Google 維護，穩定可靠
- 支持多種語言

**缺點**：
- PR 流程較重
- 配置選項較少

**適用**：需要審核的正式項目

### Dogfooding 實踐

#### 成功案例：Rust

**模式**：用 Rust 編譯 Rust

**優勢**：
- 驗證語言能力
- 發現實際痛點
- 強化生態系

**挑戰**：
- 構建複雜性高（多階段 bootstrap）
- 新功能需等待穩定版

#### 演進案例：TypeScript

**歷史**：用 TypeScript 編譯 TypeScript

**近期變化**（2025）：
- 部分模組用 Go 重寫
- 性能提升 10 倍
- 降低維護複雜度

**教訓**：Dogfooding 不是教條，性能需求可能優先

#### multi-agent-workflow 對標

**現狀**：
- ✅ 用自己的 Skills 開發自己
- ✅ 23 個開發經驗記錄
- ✅ 73 個測試覆蓋核心功能

**建議**：
- 繼續 Dogfooding
- 但保留手動模式作為 fallback
- 定期評估是否需要「逃逸艙」

### 版本一致性檢查

#### Buf（Protocol Buffers）

**功能**：
- 自動檢測破壞性變更
- 比較 proto 檔案版本
- 生成相容性報告

**整合方式**：
```yaml
# buf.yaml
breaking:
  use:
    - FILE
```

#### openapi-diff

**功能**：
- 比較 OpenAPI 規格
- 識別破壞性 vs 非破壞性變更
- 生成變更報告

#### 應用到 Plugin 開發

**建議**：
- 為 plugin.json 建立 schema
- 每次發布前檢查 schema 相容性
- 自動標記破壞性變更（MAJOR bump）

### 熱載入開發模式

#### 跨平台監控策略

| 平台 | 工具 | 優點 |
|------|------|------|
| macOS | fswatch | 原生、高效 |
| Linux | inotifywait | 原生、穩定 |
| Windows | polling | 通用、慢 |

**最佳實踐**：
```bash
# 優先順序降級
if command -v fswatch &> /dev/null; then
    watch_with_fswatch
elif command -v inotifywait &> /dev/null; then
    watch_with_inotifywait
else
    watch_with_polling
fi
```

#### 防抖動配置

**標準值**：500ms

**原因**：
- 文件系統事件可能連續觸發
- 編輯器保存可能產生多次寫入
- 防止過度同步

#### 增量同步

**Hash-based 快取映射**：
```json
{
  "skills/research/SKILL.md": {
    "hash": "sha256:...",
    "size": 12345,
    "mtime": 1706789012
  }
}
```

**效益**：
- 大型 Plugin 同步時間從 ~2s 降至 <100ms
- 減少 I/O 操作
- 準確追蹤變更

## 業界最佳實踐

| 領域 | 做法 | 適用場景 |
|------|------|---------|
| **版本管理** | Semantic Versioning + 自動偵測破壞性變更 | 所有 Plugin |
| **Monorepo 發布** | pnpm workspaces + changesets | 多 Skill 系統 |
| **CI/CD 工作流** | GitHub Actions + 草稿發布 + 自動簽名 | IDE 和 CLI Plugin |
| **熱載入** | 多層監控工具 + 防抖動 | 開發模式 |
| **增量同步** | Hash-based 快取映射 | 大型 Plugin |

## 建議採納的模式

### 1. 發布狀態機（JetBrains 模式）

**步驟**：
```
驗證 → 測試 → Git 檢查 → 版本升級 →
Changelog → Commit → Tag → Push
```

**特點**：
- 原子步驟
- 支持失敗恢復（progress 持久化）

### 2. 版本檔案同步一致性檢查

**檢查點**：
- plugin.json
- marketplace.json
- CLAUDE.md 中的版本

**自動偵測**：VersionConflictError

### 3. Conventional Commits + 自動分類

| Commit 類型 | 版本影響 |
|------------|---------|
| feat(scope): | MINOR |
| fix(scope): | PATCH |
| BREAKING CHANGE: | MAJOR |

### 4. 跨平台熱載入

**優先級**：fswatch → inotifywait → polling

**配置**：
- 防抖動：500ms
- 排除：`__pycache__`、`.git`、`*.pyc`

### 5. 增量同步快取策略

**存儲**：`.plugin-dev/cache-map.json`

**追蹤**：hash + size + mtime

## 現有實現的評估

### 強項

✓ Semantic Versioning 規範正確
✓ Conventional Commit 解析完善
✓ Git 工作流自動化
✓ 多文件版本同步
✓ 跨平台熱載入
✓ Hash-based 增量同步

### 可改進

- [ ] 破壞性變更自動偵測（API diff 分析）
- [ ] 版本一致性強制檢查（pre-commit hook）
- [ ] 遠程兼容性檢查
- [ ] Monorepo 支持（多 plugin.json 協調發布）

## 結論

multi-agent-workflow 的 Plugin 開發工具已建立堅實基礎。

**與業界標準對比**：
| 領域 | 評價 |
|------|------|
| 版本管理 | ✓ 達到業界水準 |
| 自動化發布 | ✓ 達到業界水準（8 步流程）|
| 熱載入開發 | ✓ 超過業界標準（三層監控）|
| 增量同步 | ✓ 業界領先（Hash-based）|

**主要建議**：
1. 集成破壞性變更自動偵測
2. 採用 changesets 風格的版本分離
3. 添加發布狀態恢復機制
4. 將 Git 操作統一到 git_lib

---

*由業界實踐研究員視角產出*

## 參考來源

- VS Code Extension Development Guide 2026
- JetBrains Plugin Developers Newsletter Q4 2025
- npm Release Automation Best Practices
- Rust Compiler Development Guide - Bootstrapping
- Homebrew Formula Authors Documentation
- Buf Breaking Change Detection
- Compose Hot Reload 1.0.0 Release Notes
- Monorepo Guide: pnpm + Changesets
