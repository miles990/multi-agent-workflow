# 風險分析師報告

> plugin-dev Skill 實作風險評估與緩解策略

**視角**：風險分析師
**日期**：2026-02-01
**階段**：PLAN

## 執行摘要

本報告針對 plugin-dev Skill 實作進行全面風險評估，識別 **12 個關鍵風險**。整體風險水平為**中等可控**，通過適當緩解措施可降至可接受範圍。

**風險分布**：
- P1 高優先級：3 個（需立即處理）
- P2 中優先級：6 個（2-4 週內處理）
- P3 低優先級：3 個（持續監控）

## 風險清單

| ID | 風險名稱 | 機率 | 影響 | 嚴重度 | 優先級 |
|----|---------|------|------|--------|--------|
| R1 | Dogfooding 循環依賴導致開發中斷 | Medium | Critical | **High** | **P1** |
| R2 | git_lib 整合引入 Bug | High | High | **High** | **P1** |
| R3 | Claude Code API 變更破壞功能 | Medium | Critical | **High** | **P1** |
| R4 | 跨平台監控工具不可用 | High | Medium | Medium | P2 |
| R5 | 同步中斷導致快取不一致 | Medium | Medium | Medium | P2 |
| R6 | 發布流程中斷導致版本混亂 | Low | High | Medium | P2 |
| R7 | 快取損壞無法自動修復 | Low | Medium | Medium | P2 |
| R8 | 版本相容性檢測誤判 | Medium | Low | Low | P2 |
| R9 | 測試覆蓋不足導致 Regression | Medium | Medium | Medium | P2 |
| R10 | 檔案監控效能問題 | Low | Medium | Low | P3 |
| R11 | Git 操作失敗無法恢復 | Low | High | Medium | P2 |
| R12 | 配置變更導致向後不相容 | Low | Medium | Low | P3 |

## 風險詳情

### R1: Dogfooding 循環依賴（P1 - HIGH）

**描述**：使用 `/plugin-dev` 開發自己時，若核心功能損壞，可能無法修復。

**場景**：
1. 修改 CacheManager 引入 Bug → 同步失敗 → 無法載入修復代碼
2. ReleaseCommands 損壞 → 無法發布修復版本
3. Skill 載入邏輯錯誤 → Claude Code 無法執行命令

**緩解策略**：

1. **雙軌制開發**（立即實施）
   ```bash
   # 方案 A: 獨立 Shell 腳本（fallback）
   ./scripts/plugin/sync-to-cache.sh

   # 方案 B: Skill 命令
   /plugin-dev sync
   ```

2. **Git 分支保護**
   - 新功能在 feature 分支開發
   - 充分測試後才合併到 main

3. **自檢機制**
   ```python
   def pre_execution_check():
       """執行前自檢，快速失敗"""
       checks = [
           ("cache_manager", CacheManager().get_cache_dir),
           ("version_manager", VersionManager().get_current_version),
       ]
       for name, check_fn in checks:
           try:
               check_fn()
           except Exception as e:
               print(f"⚠️ {name} 自檢失敗，請使用 fallback 腳本")
               raise SystemExit(1)
   ```

**殘留風險**：10%，可接受（Git 回退成本低）

### R2: git_lib 整合引入 Bug（P1 - HIGH）

**描述**：release.py 從 subprocess 遷移到 git_lib 可能引入行為不一致。

**場景**：
1. Commit message 格式變更（git_lib 添加 Co-Author）
2. Pathspec 語法差異
3. 錯誤處理方式不同

**緩解策略**：

1. **整合測試**（Week 2）
   ```python
   def test_git_lib_integration():
       facade = WorkflowCommitFacade(project_dir)
       facade.commit_with_message("test: integration")
       last_commit = git_log("-1", "--format=%B")
       assert "Co-Authored-By" in last_commit
   ```

2. **漸進式遷移**
   - 建立 GitLibAdapter 適配層
   - 逐步替換 subprocess 調用
   - 每步驗證行為一致

3. **回退計劃**
   - 保留原始代碼作為註解
   - Git 分支保護

**殘留風險**：15%，需持續監控

### R3: Claude Code API 變更（P1 - HIGH）

**描述**：Claude Code 更新可能變更快取路徑或 Plugin 載入機制。

**緩解策略**：

1. **路徑自動檢測**
   ```python
   class CacheDetector:
       FALLBACK_PATTERNS = [
           "~/.claude/plugins/cache/{marketplace}/{plugin}/{version}/",
           "~/.claude/plugins/v2/{hash}/",
           "~/Library/Application Support/Claude/plugins/",
       ]

       def detect(self, plugin_name: str) -> Optional[Path]:
           for pattern in self.FALLBACK_PATTERNS:
               path = self._expand(pattern, plugin_name)
               if path.exists():
                   return path
           return self._search_filesystem(plugin_name)
   ```

2. **手動配置選項**
   ```yaml
   cache:
     auto_detect: true
     manual_override: null  # 用戶可手動設定
   ```

3. **版本相容性矩陣**
   - 文檔列出支援的 Claude Code 版本
   - 每次更新後執行相容性測試

**殘留風險**：20%，有逃生門

### R4-R12: 中低優先級風險

| 風險 | 緩解狀態 | 關鍵措施 |
|------|---------|---------|
| R4 跨平台監控 | 已緩解 | 三層降級：fswatch → inotifywait → polling |
| R5 同步中斷 | 部分緩解 | 原子性同步 + 狀態追蹤 |
| R6 發布中斷 | 已緩解 | ReleaseProgress 狀態機 + --resume |
| R7 快取損壞 | 已緩解 | validate() + repair() |
| R8 版本誤判 | 未緩解 | TODO: 實作破壞性變更檢測 |
| R9 測試覆蓋 | 部分緩解 | 需添加整合測試和端到端測試 |
| R10 監控效能 | 已緩解 | 防抖動 + 排除規則 |
| R11 Git 失敗 | 已緩解 | 預檢查 + 詳細錯誤訊息 |
| R12 配置不相容 | 未緩解 | TODO: 配置版本化 |

## 緩解時程

| 風險 | 優先級 | 緩解時程 | 負責模組 |
|------|--------|---------|---------|
| R1 | P1 | Week 1 | DevCommands |
| R2 | P1 | Week 2-3 | ReleaseCommands |
| R3 | P1 | Week 1-2 | CacheManager |
| R4 | P2 | Week 2-3 | dev-watch.sh |
| R5 | P2 | Week 2 | DevCommands |
| R9 | P2 | Week 2-4 | tests/ |

## 監控指標

| 類別 | 指標 | 目標 |
|------|------|------|
| 可靠性 | Skill 執行成功率 | > 99% |
| 可靠性 | 同步成功率 | > 95% |
| 可靠性 | 發布成功率 | > 90% |
| 效能 | 同步延遲 (p95) | < 3s |
| 品質 | 測試覆蓋率 | > 80% |

## 應急預案

### 預案 1: Dogfooding 導致開發癱瘓

1. 停止使用 Skill
2. 使用獨立腳本：`./scripts/plugin/sync-to-cache.sh`
3. Git 回退到最後正常 commit
4. 驗證後重新啟用

**恢復時間**：< 15 分鐘

### 預案 2: 發布後發現重大 Bug

```bash
# 回滾
./scripts/plugin/publish.sh --rollback v2.4.0

# 或手動
git revert HEAD
git push origin main
git push origin :refs/tags/v2.4.0
```

**恢復時間**：< 30 分鐘

## 風險儀表板

```
風險狀態 (更新: 2026-02-01)

| 風險 | 狀態 |
|------|------|
| R1: Dogfooding 循環依賴 | 🟡 部分緩解 |
| R2: git_lib 整合 | 🔴 未緩解 |
| R3: Claude Code 變更 | 🟡 部分緩解 |
| R4: 跨平台監控 | 🟢 已緩解 |
| R5: 同步中斷 | 🟡 部分緩解 |
| R6: 發布中斷 | 🟢 已緩解 |

🟢 已緩解  🟡 部分緩解  🔴 未緩解
```

## 總結

**整體風險水平**：中等可控

**成功標準**（v1.0.0 發布前）：
- P1 風險全部緩解
- P2 風險 80% 緩解
- 測試覆蓋率 > 80%
- 跨平台驗證通過

---

*由風險分析師視角產出*
