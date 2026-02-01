# Implement 視角定義

本 Skill 的視角定義集中管理於 `shared/perspectives/catalog.yaml`。

## 引用方式

```yaml
# 從 catalog.yaml 載入本 skill 適用的視角
perspectives:
  source: shared/perspectives/catalog.yaml
  filter:
    category: implement
  preset: standard  # 預設使用 4 視角
```

## 視角列表

### 標準模式 (4 視角)

| ID | 名稱 | 關注重點 | 模型層級 | 方法 |
|----|------|----------|----------|------|
| `tdd-enforcer` | TDD 守護者 | 測試先行和覆蓋率監督 | haiku | observe |
| `performance-optimizer` | 效能優化師 | 時間複雜度和記憶體效能 | sonnet | observe |
| `security-auditor` | 安全審計員 | OWASP 和安全最佳實踐 | sonnet | observe |
| `maintainer` | 維護性專家 | 可讀性和重構友善度 | haiku | observe |

### 快速模式 (2 視角)

| ID | 名稱 | 關注重點 |
|----|------|----------|
| `tdd-enforcer` | TDD 守護者 | 測試先行和覆蓋率監督 |
| `security-auditor` | 安全審計員 | OWASP 和安全最佳實踐 |

### 深度模式 (6 視角)

標準 4 視角 + 跨領域視角：

| ID | 名稱 | 關注重點 |
|----|------|----------|
| `i18n-specialist` | 國際化專家 | 多語言支援、本地化、文化適應 |
| `accessibility-specialist` | 無障礙專家 | WCAG 合規和無障礙設計 |

## 視角協作模式

```
┌─────────────────────────────────────────────────────────┐
│                    主 Agent 實作                         │
├─────────────────────────────────────────────────────────┤
│  品質層                          安全層                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐│
│  │ TDD      │  │ 效能     │  │ 安全     │  │ 維護性   ││
│  │ 守護者   │  │ 優化師   │  │ 審計員   │  │ 專家     ││
│  │          │  │          │  │          │  │          ││
│  │ 測試先行 │  │ 複雜度   │  │ OWASP    │  │ 可讀性   ││
│  │ 覆蓋率   │  │ 記憶體   │  │ 輸入驗證 │  │ 文檔     ││
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘│
│        ↓              ↓              ↓              ↓   │
│                    即時回饋到主 Agent                    │
└─────────────────────────────────────────────────────────┘
```

## 阻擋條件

各視角可設定阻擋條件，必須修正才能繼續：

| 視角 | 阻擋條件 |
|------|----------|
| tdd-enforcer | 新函數無測試、覆蓋率低於 80%、關鍵路徑未測試 |
| performance-optimizer | 複雜度超過 O(n^3)、記憶體洩漏、N+1 查詢 |
| security-auditor | SQL 注入風險、XSS 漏洞、硬編碼密鑰、不安全認證 |
| maintainer | 函數超過 200 行、圈複雜度超過 20、重複程式碼超過 30% |

## 回饋優先順序

1. Security 阻擋 > 其他阻擋
2. TDD 阻擋 > Performance 阻擋
3. 多視角共識 > 單視角意見

完整定義請參考 [catalog.yaml](../../../../shared/perspectives/catalog.yaml)。
