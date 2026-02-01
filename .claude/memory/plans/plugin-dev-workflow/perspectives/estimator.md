# 估算專家報告

> plugin-dev Skill 工作量評估與時程規劃

**視角**：估算專家
**日期**：2026-02-01
**階段**：PLAN

## 執行摘要

基於研究報告和現有代碼分析，plugin-dev Skill 實作預估：
- **總工作量**：89 點（Fibonacci scale）
- **預估時程**：6-8 週
- **里程碑**：4 個（MVP → 發布功能 → 完整功能 → Dogfooding 成熟）

## 現有資產

| 資產 | 規模 | 可復用性 |
|------|------|---------|
| Python 模組 (cli/plugin/) | 1,829 行 | 95% |
| Shell 腳本 (scripts/plugin/) | 1,653 行 | 70% |
| 測試 (tests/plugin/) | 73 個 | 100% |
| git_lib 模組 | 1,029 行 | 100% |
| 配置 (shared/plugin/) | ~300 行 | 100% |

## 任務分解

### Phase 1: Skill 結構建立（13 點）

| 任務 | 複雜度 | 依賴 | 說明 |
|------|--------|------|------|
| 1.1 建立 skills/plugin-dev/ 目錄 | 2 | - | 標準結構 |
| 1.2 撰寫 SKILL.md frontmatter | 3 | 1.1 | 定義觸發器、模型、工具 |
| 1.3 撰寫 00-quickstart/usage.md | 3 | 1.2 | 快速開始指南 |
| 1.4 建立 01-commands/ 目錄 | 3 | 1.2 | 命令說明文檔 |
| 1.5 配置執行模式對應 | 2 | 1.2 | express/default/quality |

### Phase 2: 核心命令實作（21 點）

| 任務 | 複雜度 | 依賴 | 說明 |
|------|--------|------|------|
| 2.1 實作 `/plugin-dev sync` | 5 | 1.2 | 使用現有 DevCommands.sync() |
| 2.2 實作 `/plugin-dev validate` | 3 | 1.2 | 使用現有 ReleaseCommands.validate() |
| 2.3 實作 `/plugin-dev status` | 3 | 1.2 | 聚合 CacheManager + VersionManager |
| 2.4 建立 Skill 框架類別 | 5 | 1.2 | 命令路由、參數解析 |
| 2.5 配置載入機制 | 5 | 1.2 | PluginConfig 類別 |

### Phase 3: git_lib 整合（13 點）

| 任務 | 複雜度 | 依賴 | 說明 |
|------|--------|------|------|
| 3.1 建立 GitLibAdapter | 5 | - | 適配層 |
| 3.2 修改 release.py | 5 | 3.1 | 替換 subprocess 調用 |
| 3.3 統一 commit message 格式 | 3 | 3.2 | Co-Author 處理 |

### Phase 4: 發布流程實作（21 點）

| 任務 | 複雜度 | 依賴 | 說明 |
|------|--------|------|------|
| 4.1 實作 `/plugin-dev release` | 5 | 2.4, 3.2 | 主命令 |
| 4.2 完善狀態機 | 5 | 4.1 | ReleaseProgress 完整實作 |
| 4.3 Task API 整合 | 5 | 4.1 | 進度追蹤 |
| 4.4 進度持久化 | 3 | 4.2 | JSON 保存/載入 |
| 4.5 錯誤恢復機制 | 3 | 4.4 | --resume 功能 |

### Phase 5: 熱載入實作（13 點）

| 任務 | 複雜度 | 依賴 | 說明 |
|------|--------|------|------|
| 5.1 實作 `/plugin-dev watch` | 5 | 2.4 | 主命令 |
| 5.2 跨平台監控整合 | 5 | 5.1 | fswatch/inotifywait/polling |
| 5.3 背景執行支援 | 3 | 5.1 | run_in_background |

### Phase 6: 文檔與 Dogfooding（8 點）

| 任務 | 複雜度 | 依賴 | 說明 |
|------|--------|------|------|
| 6.1 更新 CLAUDE.md | 3 | 4.5, 5.3 | 開發經驗記錄 |
| 6.2 撰寫完整教程 | 2 | 6.1 | 從零開始指南 |
| 6.3 Dogfooding 驗證 | 3 | 6.1 | 用自己開發自己 |

## 里程碑

### M1: MVP（Week 2）

**交付物**：
- `/plugin-dev sync` 可用
- `/plugin-dev validate` 可用
- `/plugin-dev status` 可用
- 基本文檔

**驗收標準**：
- 可取代 `./scripts/plugin/sync-to-cache.sh`
- 測試覆蓋率 > 70%

**工作量**：34 點（Phase 1 + Phase 2）

### M2: 發布功能（Week 4）

**交付物**：
- `/plugin-dev release [level]` 可用
- git_lib 完整整合
- 進度持久化和恢復

**驗收標準**：
- 可取代 `./scripts/plugin/publish.sh`
- 支援 --dry-run 和 --resume
- 測試覆蓋率 > 80%

**工作量**：34 點（Phase 3 + Phase 4）

### M3: 完整功能（Week 6）

**交付物**：
- `/plugin-dev watch` 可用
- 跨平台驗證通過
- 背景執行支援

**驗收標準**：
- macOS/Linux 監控正常
- Windows polling 模式可用
- 效能指標達標

**工作量**：13 點（Phase 5）

### M4: Dogfooding 成熟（Week 8）

**交付物**：
- 完整文檔
- CLAUDE.md 更新
- 用 plugin-dev 開發 plugin-dev

**驗收標準**：
- 新手 30 分鐘內上手
- Dogfooding 無阻礙
- 所有 P1/P2 風險已緩解

**工作量**：8 點（Phase 6）

## 依賴關係

```
Phase 1 (Skill 結構)
    │
    ▼
Phase 2 (核心命令) ────────┐
    │                      │
    ▼                      ▼
Phase 3 (git_lib) ──► Phase 4 (發布流程)
    │                      │
    └──────────────────────┼──► Phase 5 (熱載入)
                           │        │
                           ▼        ▼
                      Phase 6 (文檔 + Dogfooding)
```

**並行機會**：
- Phase 3 和 Phase 5 可並行（獨立功能）
- Phase 2 內的 3 個命令可並行

## 時程建議

| 週次 | 主要工作 | 里程碑 |
|------|---------|--------|
| Week 1 | Phase 1: Skill 結構 | - |
| Week 2 | Phase 2: 核心命令 | **M1: MVP** |
| Week 3 | Phase 3: git_lib 整合 | - |
| Week 4 | Phase 4: 發布流程 | **M2: 發布功能** |
| Week 5 | Phase 5: 熱載入 | - |
| Week 6 | Phase 5 完成 + 測試 | **M3: 完整功能** |
| Week 7 | Phase 6: 文檔 | - |
| Week 8 | Dogfooding + 修復 | **M4: 成熟** |

## 資源需求

| 角色 | 技能要求 | 涉及 Phase |
|------|---------|-----------|
| Python 開發 | Python, 設計模式 | 1-4, 6 |
| Shell 開發 | Bash, 跨平台 | 5 |
| 測試工程 | pytest, 整合測試 | 全部 |
| 文檔撰寫 | Markdown | 6 |

## 風險調整

| 風險 | 影響 | 緩衝 |
|------|------|------|
| git_lib 整合複雜度 | +3 點 | Week 3 可延長 |
| 跨平台相容性問題 | +5 點 | Week 5-6 緩衝 |
| Dogfooding 發現問題 | +8 點 | Week 7-8 修復窗口 |

**總緩衝**：16 點（~18% buffer）

## 品質閘門檢查

### TASKS 階段閘門（≥80 分）

| 檢查項 | 狀態 |
|--------|------|
| DAG 無循環依賴 | ✅ |
| 每個 Phase 有測試任務 | ✅ |
| 所有任務有點數估算 | ✅ |
| 任務粒度 3-21 點 | ✅ |
| 里程碑定義清晰 | ✅ |
| 依賴關係完整 | ✅ |

**預估品質分數**：85/100

## 總結

| 指標 | 數值 |
|------|------|
| 總工作量 | 89 點 |
| 預估時程 | 6-8 週 |
| 里程碑數 | 4 |
| 任務數 | 18 |
| 並行度 | 中等 |

**建議**：
- 優先完成 M1 (MVP) 以獲得早期反饋
- Phase 3 和 Phase 5 可並行執行
- 預留 Week 7-8 作為修復緩衝

---

*由估算專家視角產出*
