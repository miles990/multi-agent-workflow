# Plugin 開發測試發布流程優化 - 實作計劃

## 執行摘要

設計一套完整的 Plugin 開發工作流系統,涵蓋開發、測試、版本管理、發布、安裝更新等全生命週期,遵循 DRY、SOLID 原則,提供優雅、可靠、可維護的解決方案。

## 核心目標

1. **開發效率**: 本地開發熱載入、快速測試回饋循環
2. **版本管理**: 語義化版本、變更日誌自動生成、相容性檢查
3. **發布流程**: 自動化發布、Marketplace 整合、版本標記
4. **安裝更新**: 快取管理、增量更新、回滾機制
5. **品質保證**: 自動測試、Lint、結構驗證

## 架構設計

### 1. 目錄結構

```
multi-agent-workflow/
├── cli/
│   └── plugin/                    # Plugin 管理 CLI (新增)
│       ├── __init__.py
│       ├── dev.py                 # 開發命令
│       ├── test.py                # 測試命令
│       ├── release.py             # 發布命令
│       ├── version.py             # 版本管理
│       └── cache.py               # 快取管理
├── scripts/
│   ├── plugin/                    # Plugin 工具腳本 (新增)
│   │   ├── dev-watch.sh          # 熱載入監控
│   │   ├── sync-to-cache.sh      # 同步到快取
│   │   ├── validate-plugin.sh    # Plugin 驗證
│   │   ├── bump-version.sh       # 版本升級
│   │   ├── generate-changelog.sh # 變更日誌生成
│   │   └── publish.sh            # 發布到 Marketplace
│   └── git_lib/                   # 已存在: Git 操作統一模組
├── shared/
│   └── plugin/                    # Plugin 共用模組 (新增)
│       ├── config.yaml           # Plugin 配置
│       ├── version-strategy.yaml # 版本策略
│       ├── cache-policy.yaml     # 快取策略
│       └── CLAUDE.md             # 使用說明
├── .plugin-dev/                   # 開發配置 (新增)
│   ├── watch.config.json         # 監控配置
│   ├── cache-map.json            # 快取映射
│   └── test-env.json             # 測試環境
├── tests/
│   └── plugin/                    # Plugin 測試 (新增)
│       ├── test_dev_workflow.py
│       ├── test_version_manager.py
│       ├── test_cache_manager.py
│       └── test_release.py
├── plugin.json                    # 已存在: Plugin manifest
├── .claude-plugin/
│   └── marketplace.json           # 已存在: Marketplace 配置
└── CHANGELOG.md                   # 變更日誌 (新增)
```

### 2. 核心模組設計

#### 2.1 Plugin CLI (cli/plugin/)

公開 API:
- plugin dev watch - 啟動熱載入開發模式
- plugin dev sync - 手動同步到快取
- plugin dev link - 建立符號連結(進階)
- plugin test - 執行 Plugin 測試
- plugin test --integration - 整合測試
- plugin version show - 顯示當前版本
- plugin version bump [major|minor|patch] - 升級版本
- plugin version check-compat - 檢查相容性
- plugin release - 發布到 Marketplace
- plugin release --dry-run - 模擬發布
- plugin cache clean - 清理快取
- plugin cache status - 快取狀態

設計考量:
- 增量同步: 只同步變更檔案,提升效率
- 檔案過濾: 排除測試、文檔、Git 等無關檔案
- 錯誤處理: 快取目錄不存在時友善提示
- 跨平台: 支援 macOS/Linux/Windows 路徑差異

#### 2.2 版本管理 (cli/plugin/version.py)

核心功能:
1. bump(level) - 升級版本號
   - 讀取 plugin.json 當前版本
   - 根據語義化版本規則升級
   - 更新 plugin.json, marketplace.json, CLAUDE.md
   - 建議 Git commit message

2. check_compatibility(target_version) - 檢查相容性
   - 分析版本差異,檢測破壞性變更
   - API 移除/重命名
   - 必要參數變更
   - 配置格式變更

3. generate_changelog(since_tag) - 生成變更日誌
   - 從 Git commits 提取
   - feat: 新功能
   - fix: Bug 修復
   - breaking: 破壞性變更
   - docs: 文檔更新

#### 2.3 快取管理 (cli/plugin/cache.py)

核心功能:
- get_cache_dir(plugin_name) - 取得 Plugin 快取目錄
- clean(plugin_name) - 清理快取
- status() - 快取狀態(大小、同步時間、檔案數量、版本)
- validate() - 驗證快取完整性

快取策略:
- 位置: ~/.claude/plugins/cache/
- 同步模式: incremental (hash-based)
- 排除規則: __pycache__, *.pyc, .git, tests等
- 保留最近 3 個版本
- 自動清理

#### 2.4 發布流程 (cli/plugin/release.py)

發布工作流程:
1. 驗證 Plugin 結構
2. 執行測試
3. 檢查 Git 狀態(無未提交變更)
4. 升級版本(互動選擇 major/minor/patch)
5. 生成變更日誌
6. Git commit + tag
7. 推送到遠端
8. 更新 .claude-plugin/marketplace.json
9. 觸發 Marketplace 同步(如有 API)

驗證檢查:
- plugin.json 完整性
- 所有 Skills 有 SKILL.md
- 測試通過
- Lint 通過
- 無未提交變更

## 實作階段

### Phase 1: 核心基礎設施 (優先級: HIGH)

目標: 建立 CLI 框架和快取管理

任務清單:
1. 建立目錄結構
   - cli/plugin/
   - scripts/plugin/
   - shared/plugin/
   - .plugin-dev/

2. 實作 CacheManager
   - 定義快取路徑常數
   - 實作 get_cache_dir()
   - 實作 status() 顯示快取資訊
   - 實作 clean() 清理快取
   - 實作 validate() 驗證完整性

3. 實作同步腳本
   - scripts/plugin/sync-to-cache.sh
   - 使用 rsync 增量同步
   - 讀取排除規則從配置檔案
   - 錯誤處理和日誌

4. 建立配置檔案
   - .plugin-dev/watch.config.json
   - .plugin-dev/cache-map.json
   - shared/plugin/cache-policy.yaml

驗收標準:
- plugin cache status 顯示快取資訊
- plugin cache clean 清理快取
- sync-to-cache.sh 成功同步到快取
- 單元測試覆蓋率 >= 80%

估算: 2-3 天

---

### Phase 2: 開發工作流 (優先級: HIGH)

目標: 實現熱載入開發模式

任務清單:
1. 實作 DevCommands
   - dev.sync() - 手動同步
   - dev.watch() - 熱載入監控
   - dev.link() - 符號連結(可選)

2. 實作監控腳本
   - scripts/plugin/dev-watch.sh
   - 平台檢測(macOS/Linux)
   - 使用 fswatch 或 inotifywait
   - 防抖動邏輯(避免頻繁觸發)

3. CLI 整合
   - 註冊 plugin dev 子命令
   - 參數解析和驗證
   - 友善的錯誤訊息

4. 快取映射記錄
   - 更新 .plugin-dev/cache-map.json
   - 記錄檔案 hash、大小、時間戳
   - 僅同步變更檔案

驗收標準:
- plugin dev watch 監控檔案變更並自動同步
- plugin dev sync 手動同步成功
- 修改檔案後 1 秒內同步到快取
- 排除規則正確生效
- 跨平台測試(macOS + Linux)

估算: 3-4 天

---

### Phase 3: 版本管理 (優先級: MEDIUM)

目標: 語義化版本控制和變更日誌

任務清單:
1. 實作 VersionManager
   - bump() - 升級版本號
   - check_compatibility() - 相容性檢查
   - generate_changelog() - 變更日誌生成

2. 實作版本升級腳本
   - scripts/plugin/bump-version.sh
   - 更新 plugin.json
   - 更新 marketplace.json
   - 更新 CLAUDE.md 版本聲明

3. 實作變更日誌生成
   - scripts/plugin/generate-changelog.sh
   - 從 Git commits 提取
   - 分類: Added, Fixed, Changed, Breaking
   - 合併到 CHANGELOG.md

4. 定義版本策略
   - shared/plugin/version-strategy.yaml
   - 定義 major/minor/patch 規則
   - 破壞性變更檢測規則
   - 棄用政策

驗收標準:
- plugin version bump patch 正確升級版本
- 所有相關檔案同步更新
- plugin version check-compat 檢測破壞性變更
- CHANGELOG.md 自動生成
- Git commit message 建議

估算: 2-3 天

---

### Phase 4: 發布流程 (優先級: MEDIUM)

目標: 自動化發布到 Marketplace

任務清單:
1. 實作 ReleaseCommands
   - release() - 完整發布流程
   - validate() - 發布前驗證

2. 實作發布腳本
   - scripts/plugin/publish.sh
   - Git commit + tag
   - 推送到遠端
   - 更新 Marketplace(如有 API)

3. 實作驗證工具
   - scripts/plugin/validate-plugin.sh
   - 檢查 plugin.json 完整性
   - 檢查所有 Skills 結構
   - 執行測試
   - 檢查 Git 狀態

4. 發布檢查清單
   - 測試通過
   - Lint 通過
   - 文檔更新
   - 變更日誌生成
   - 版本升級
   - 無未提交變更

驗收標準:
- plugin release --dry-run 模擬發布成功
- plugin release 完整發布流程執行無誤
- Git tag 正確建立
- Marketplace 配置更新
- 發布檢查清單全部通過

估算: 2-3 天

---

### Phase 5: 測試與文檔 (優先級: LOW)

目標: 完善測試覆蓋率和文檔

任務清單:
1. 單元測試
   - tests/plugin/test_cache_manager.py
   - tests/plugin/test_version_manager.py
   - tests/plugin/test_dev_workflow.py
   - tests/plugin/test_release.py

2. 整合測試
   - 完整開發工作流測試
   - 完整發布工作流測試
   - 跨平台測試

3. 文檔更新
   - 更新 CLAUDE.md 開發工作流章節
   - 更新 README.md 安裝與使用
   - 新增 shared/plugin/CLAUDE.md 使用說明
   - 新增 docs/plugin-development.md 開發指南

4. 範例與教學
   - 快速開始範例
   - 版本升級範例
   - 發布流程範例

驗收標準:
- 測試覆蓋率 >= 85%
- 所有文檔更新完成
- 範例可執行無誤
- CI/CD 整合

估算: 2-3 天


## 技術設計細節

### 1. 熱載入實作方案

方案 A: 檔案監控 + rsync (推薦)

優點:
- 增量同步,效率高
- 跨平台支援良好
- 實作簡單

缺點:
- 需要額外工具(fswatch/inotifywait)
- 有輕微延遲(< 1s)

方案 B: 符號連結

優點:
- 零延遲
- 無需同步

缺點:
- Windows 需要管理員權限
- Claude Code 可能不支援

選擇: 方案 A 為預設,方案 B 為進階選項

### 2. 版本相容性檢查

檢測策略:

1. 靜態分析:
   - 比較 plugin.json 的 API 聲明
   - 比較 SKILL.md 的參數定義
   - 比較配置檔案 schema

2. 語義分析:
   - 解析 Git diff
   - 識別函數/類別刪除
   - 識別必要參數新增

3. 人工標記:
   - Commit message 包含 "BREAKING CHANGE:"
   - CHANGELOG.md 手動標記

### 3. 快取策略

同步模式:

| 模式 | 檢查方法 | 適用場景 |
|------|----------|----------|
| incremental | hash | 日常開發(推薦)|
| full | - | 初次同步、版本切換 |
| timestamp | mtime | 快速但不精確 |

排除規則優先順序:
1. .plugin-dev/watch.config.json 自訂規則
2. shared/plugin/cache-policy.yaml 全域規則
3. .gitignore 繼承規則

### 4. 發布工作流

```
開始發布 -> 驗證 Plugin -> 執行測試 -> 檢查 Git 狀態
    -> 互動選擇版本升級 -> 升級版本號 -> 生成變更日誌
    -> Git commit -> 建立 Git tag -> 推送到遠端
    -> 更新 Marketplace -> 發布成功
```

## 風險評估與緩解

### 風險 1: Claude Code 快取機制變更

機率: Medium  
影響: High  
緩解:
- 抽象快取路徑為可配置項
- 提供檢測腳本自動發現快取位置
- 文檔說明手動修改配置方法

### 風險 2: 跨平台相容性

機率: Medium  
影響: Medium  
緩解:
- 使用跨平台工具(rsync、Python)
- 平台檢測和自動選擇工具
- CI/CD 在多平台測試

### 風險 3: 檔案監控效能問題

機率: Low  
影響: Medium  
緩解:
- 防抖動邏輯(debounce 500ms)
- 排除大目錄(node_modules, .git)
- 提供關閉自動同步選項

### 風險 4: 版本相容性誤判

機率: Medium  
影響: Low  
緩解:
- 多層檢測機制(靜態+語義+人工)
- 提供 override 選項
- 人工審核流程

## 品質標準

### 程式碼品質

| 指標 | 目標 | 檢查方式 |
|------|------|----------|
| 測試覆蓋率 | >= 85% | pytest --cov |
| Lint | 0 errors | ruff check |
| Type Check | 0 errors | mypy |
| 複雜度 | <= 10 | radon cc -a |

### 使用者體驗

| 指標 | 目標 |
|------|------|
| 同步延遲 | < 1s |
| CLI 回應時間 | < 100ms |
| 錯誤訊息清晰度 | 包含原因 + 建議 |
| 文檔完整性 | 每個命令有範例 |

### 可靠性

| 指標 | 目標 |
|------|------|
| 同步成功率 | >= 99.9% |
| 版本升級成功率 | 100% |
| 快取一致性 | 100% |

## 文檔更新計劃

### CLAUDE.md 更新

新增章節 "Plugin 開發工作流":

1. 快速開始
   - 啟動開發模式: plugin dev watch
   - 修改程式碼自動同步
   - 重啟 Claude Code 載入新版本
   - 發布新版本: plugin release

2. 詳細指南
   - 命令列表和說明
   - 連結到詳細文檔

### README.md 更新

新增章節 "For Plugin Developers":

1. Setup Development Environment
   - Clone repository
   - Install dependencies
   - Start development mode

2. Release Workflow
   - Make changes and test
   - Bump version
   - Release

3. 連結到 Plugin Development Guide

### 新增文檔

1. shared/plugin/CLAUDE.md
   - Plugin 配置說明
   - 版本策略說明
   - 快取策略說明

2. docs/plugin-development.md
   - 完整開發指南
   - 命令詳解
   - 最佳實踐
   - 疑難排解

## 成功指標

### 開發效率提升

| 指標 | 現況 | 目標 |
|------|------|------|
| 修改->測試循環 | 手動複製,~2min | 自動同步,< 1s |
| 版本發布時間 | 手動 15+ 步驟,~30min | 一鍵發布,< 5min |
| 錯誤修復回饋 | 發現後 1-2 天 | 即時檢測 |

### 品質提升

| 指標 | 現況 | 目標 |
|------|------|------|
| 版本不一致問題 | 偶爾發生 | 0 |
| 破壞性變更未通知 | 有 | 自動檢測 + 警告 |
| 文檔過時 | 有 | 自動更新 |

### 使用者滿意度

| 指標 | 目標 |
|------|------|
| 開發者上手時間 | < 10 分鐘 |
| CLI 學習曲線 | 直覺易懂 |
| 錯誤排除時間 | < 5 分鐘 |

## 未來擴展

### Phase 6+: 進階功能 (可選)

1. A/B 測試支援
   - 多版本並存
   - 流量分配
   - 效果分析

2. 效能分析
   - Skill 執行時間追蹤
   - 熱點識別
   - 優化建議

3. 依賴管理
   - Skill 間依賴聲明
   - 版本相容性矩陣
   - 自動升級建議

4. Marketplace API 整合
   - 自動上傳
   - 下載統計
   - 使用者回饋收集

5. 插件範本系統
   - 快速建立新 Plugin
   - 最佳實踐範本
   - 腳手架工具

## 附錄

### A. 相關技術文檔

- Git 操作統一模組: scripts/git_lib/README.md
- Skill 結構標準: shared/skill-structure/STANDARD.md
- 視角系統: shared/perspectives/CLAUDE.md
- 配置索引: shared/config/CLAUDE.md

### B. 參考專案

- semantic-release: 自動化版本管理
- Commitizen: Commit message 標準化
- watchdog: 跨平台檔案監控

### C. 決策記錄

| 決策 | 理由 |
|------|------|
| 使用 rsync 而非自訂同步 | 成熟穩定、跨平台支援佳 |
| Python CLI 而非 Bash | 更好的錯誤處理、跨平台 |
| 語義化版本 | 業界標準、相容性明確 |
| Git-based 變更日誌 | 單一事實來源、自動化 |

---

計劃版本: 1.0  
建立日期: 2026-02-01  
作者: 系統架構師 (Planning Agent)  
狀態: 待審核
