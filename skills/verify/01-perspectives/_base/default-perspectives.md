# Verify 視角定義

本 Skill 的視角定義集中管理於 `shared/perspectives/catalog.yaml`。

## 引用方式

```yaml
# 從 catalog.yaml 載入本 skill 適用的視角
perspectives:
  source: shared/perspectives/catalog.yaml
  filter:
    category: verify
  preset: standard  # 預設使用 4 視角
```

## 視角列表

### 標準模式 (4 視角)

| ID | 名稱 | 關注重點 | 模型層級 | 方法 |
|----|------|----------|----------|------|
| `functional-tester` | 功能測試員 | 核心功能和 Happy Path 驗證 | haiku | deep |
| `edge-case-hunter` | 邊界獵人 | 極端輸入和錯誤處理 | sonnet | deep |
| `regression-checker` | 回歸檢查員 | 現有功能和向後相容驗證 | haiku | explore |
| `acceptance-validator` | 驗收驗證員 | 需求符合度和 DoD 確認 | sonnet | deep |

### 快速模式 (2 視角)

| ID | 名稱 | 關注重點 |
|----|------|----------|
| `functional-tester` | 功能測試員 | 核心功能和 Happy Path 驗證 |
| `acceptance-validator` | 驗收驗證員 | 需求符合度和 DoD 確認 |

### 深度模式 (6 視角)

標準 4 視角 + 專用視角：

| ID | 名稱 | 關注重點 |
|----|------|----------|
| `performance-tester` | 效能測試員 | 負載測試、壓力測試、效能基準 |
| `security-tester` | 安全測試員 | 滲透測試、漏洞掃描、安全驗證 |

## 視角協作模式

```
┌─────────────────────────────────────────────────────────┐
│                    功能驗證                              │
├─────────────────────────────────────────────────────────┤
│  功能層                          品質層                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐│
│  │ 功能     │  │ 邊界     │  │ 回歸     │  │ 驗收     ││
│  │ 測試員   │  │ 獵人     │  │ 檢查員   │  │ 驗證員   ││
│  │          │  │          │  │          │  │          ││
│  │ 核心功能 │  │ 極端輸入 │  │ 現有功能 │  │ 需求符合 ││
│  │ 使用流程 │  │ 錯誤處理 │  │ API 相容 │  │ DoD 驗證 ││
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘│
└─────────────────────────────────────────────────────────┘
```

## 視角組合策略

| 場景 | 推薦組合 | 說明 |
|------|----------|------|
| 快速驗證 | functional-tester + acceptance-validator | 核心功能 + 驗收確認 |
| 安全敏感 | edge-case-hunter + regression-checker | 邊界測試 + 回歸確認 |
| 發布驗證 | 全部 4 視角 | 預設模式 |

## 驗證輸出格式

各視角產出包含：
- 測試案例列表
- 測試結果（PASS/FAIL/REGRESSION）
- 問題清單
- 改進建議

完整定義請參考 [catalog.yaml](../../../../shared/perspectives/catalog.yaml)。
