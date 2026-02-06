# Custom Perspectives Guide

> 如何自訂視角以符合特定需求

## 何時需要自訂視角

### 場景 1: 領域特定專案

當你的專案屬於特定領域，需要專門的分析視角：

- 醫療系統：合規性視角、隱私保護視角
- 金融系統：審計視角、風控視角
- IoT 系統：硬體整合視角、即時性視角

### 場景 2: 特殊需求

當預設視角無法涵蓋你的特殊需求：

- 國際化需求：本地化視角
- 無障礙需求：可訪問性視角
- 效能關鍵：效能優化視角

### 場景 3: 團隊偏好

當你的團隊有特定的工作方式：

- 文檔優先團隊：文檔視角
- API 優先團隊：API 設計視角

## 自訂視角結構

### 基本結構

```yaml
# custom-perspectives.yaml
perspectives:
  - id: {{perspective-id}}
    name: {{視角名稱}}
    role: {{角色稱謂}}
    model: sonnet|haiku|opus
    focus:
      - {{關注點 1}}
      - {{關注點 2}}
      - {{關注點 3}}
    prompt_template: |
      你是一位{{角色稱謂}}。針對「{feature}」功能，請進行{{分析類型}}：

      1. **{{面向 1}}**：{{引導問題 1}}
      2. **{{面向 2}}**：{{引導問題 2}}
      3. **{{面向 3}}**：{{引導問題 3}}

      產出格式：
      - {{產出項目 1}}
      - {{產出項目 2}}
    output: perspectives/{{perspective-id}}.md
```

### 完整範例：合規性視角

```yaml
perspectives:
  - id: compliance
    name: 合規性審查
    role: 合規專家
    model: sonnet
    focus:
      - GDPR / 個資法合規
      - 資料保留政策
      - 審計追蹤要求
      - 第三方資料處理
      - 用戶同意管理
    prompt_template: |
      你是一位資料合規專家。針對「{feature}」功能，請進行合規性審查：

      1. **個資處理**：此功能處理哪些個人資料？如何確保合規？
      2. **用戶權利**：如何支援用戶的存取、修改、刪除權利？
      3. **資料保留**：資料保留多久？刪除政策是什麼？
      4. **第三方**：是否涉及第三方資料處理？合約條款是否充分？
      5. **審計追蹤**：如何記錄資料存取和修改歷史？

      產出格式：
      - 合規性風險清單（按嚴重度排序）
      - 每個風險的緩解措施
      - 必要的技術控制
      - 文檔和政策要求
    output: perspectives/compliance.md
```

## 視角設計原則

### 1. 明確的角色定位

每個視角應該有清晰的角色：

```yaml
✅ 好的角色定位
role: 資深 DevOps 工程師
focus:
  - 容器化策略
  - CI/CD 流程
  - 監控和告警

❌ 模糊的角色定位
role: 技術專家
focus:
  - 各種技術問題
```

### 2. 聚焦的關注點

每個視角應該聚焦 3-5 個核心關注點：

```yaml
✅ 聚焦
focus:
  - API 設計一致性
  - 錯誤處理模式
  - 版本管理策略

❌ 過於廣泛
focus:
  - 所有架構問題
  - 所有設計決策
  - 所有技術選型
```

### 3. 具體的引導問題

Prompt 應該包含具體的引導問題：

```yaml
✅ 具體的引導
1. **容器化**：建議使用 Docker 還是其他方案？為什麼？
2. **編排**：是否需要 Kubernetes？還是 docker-compose 就足夠？

❌ 模糊的引導
1. 請分析容器化需求
2. 請評估編排方案
```

### 4. 清晰的產出格式

明確說明預期的產出格式：

```yaml
✅ 清晰的產出格式
產出格式：
- 部署架構圖（文字描述）
- CI/CD 流程圖
- 監控指標清單
- 告警規則建議

❌ 模糊的產出格式
產出格式：
- 分析報告
```

## 視角組合建議

### 技術導向專案

```yaml
recommended_perspectives:
  - architect      # 系統架構
  - security       # 安全性
  - performance    # 效能
  - devops         # 維運
```

### 產品導向專案

```yaml
recommended_perspectives:
  - ux-advocate    # 使用者體驗
  - api-designer   # API 設計
  - docs-writer    # 文檔
  - accessibility  # 無障礙
```

### 合規導向專案

```yaml
recommended_perspectives:
  - compliance     # 合規性
  - security       # 安全性
  - privacy        # 隱私保護
  - audit          # 審計
```

## 使用自訂視角

### 方法 1: 專案配置檔案

在專案根目錄建立 `.claude/perspectives.yaml`：

```yaml
# .claude/perspectives.yaml
skill: audit
perspectives:
  - id: custom-1
    name: 自訂視角 1
    # ... 完整配置
```

### 方法 2: 命令列參數

```bash
/{{command}} --perspectives compliance,security,privacy {{topic}}
```

### 方法 3: 互動式選擇

```bash
/{{command}} --custom {{topic}}

# 系統會詢問：
> 請選擇視角（可多選）：
> 1. [預設] architect
> 2. [預設] risk-analyst
> 3. [預設] estimator
> 4. [預設] ux-advocate
> 5. [自訂] compliance
> 6. [自訂] performance
> 7. [自訂] devops
```

## 視角模板庫

### 技術視角

- **architect**: 系統架構設計
- **security**: 安全性分析
- **performance**: 效能優化
- **scalability**: 擴展性評估
- **devops**: 維運和部署

### 流程視角

- **risk-analyst**: 風險分析
- **estimator**: 工作量估算
- **quality**: 品質保證
- **testing**: 測試策略

### 體驗視角

- **ux-advocate**: 使用者體驗
- **api-designer**: API 設計
- **docs-writer**: 文檔撰寫
- **accessibility**: 無障礙設計

### 合規視角

- **compliance**: 合規性審查
- **privacy**: 隱私保護
- **audit**: 審計要求
- **legal**: 法律風險

## 進階技巧

### 視角依賴

某些視角可能依賴其他視角的產出：

```yaml
perspectives:
  - id: architect
    # 先執行

  - id: performance
    depends_on: [architect]  # 基於架構設計進行效能分析
```

### 條件式視角

根據專案特性動態啟用視角：

```yaml
conditional_perspectives:
  - id: compliance
    condition: handles_personal_data == true

  - id: performance
    condition: expected_load > 1000_rps
```

### 視角優先級

設定視角的優先級，影響執行順序：

```yaml
perspectives:
  - id: security
    priority: high  # 優先執行

  - id: docs-writer
    priority: low   # 最後執行
```

## 最佳實踐

1. **從預設開始**：先使用預設視角，確認不足後再自訂
2. **保持聚焦**：每個視角專注於特定領域
3. **避免重複**：不同視角應該互補而非重疊
4. **測試驗證**：建立測試案例驗證視角產出
5. **持續優化**：根據實際使用效果調整 prompt

## 相關資源

- [預設視角說明](./default-perspectives.md)
- [Prompt 工程最佳實踐](../../../../shared/perspectives/prompt-engineering.md)
- [視角模板庫](../../../../shared/perspectives/templates/)
