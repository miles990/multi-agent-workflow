# Skill Templates

> 可直接使用的 Skill 結構模板

## 模板清單

### 核心模板

| 檔案 | 用途 | 說明 |
|------|------|------|
| [SKILL.md.template](./SKILL.md.template) | Skill 主檔案 | 包含 frontmatter 和所有標準段落 |
| [quickstart.md.template](./quickstart.md.template) | 快速開始指南 | 3 分鐘快速上手 |
| [perspectives.md.template](./perspectives.md.template) | 視角定義 | 預設視角配置和說明 |
| [custom-perspectives.md.template](./custom-perspectives.md.template) | 自訂視角指南 | 如何建立自訂視角 |

### 配置模板

| 檔案 | 用途 | 說明 |
|------|------|------|
| [meta.yaml.template](./meta.yaml.template) | 元數據 | Skill 執行元數據 |
| [summary.md.template](./summary.md.template) | 執行摘要 | Skill 執行結果摘要 |
| [phases.yaml.template](./phases.yaml.template) | 執行階段 | 階段定義和配置 |
| [quality-gates.yaml.template](./quality-gates.yaml.template) | 品質閘門 | 品質標準和評分 |

## 使用方式

### 快速建立新 Skill

```bash
#!/bin/bash
# 腳本：create-skill.sh

SKILL_NAME=$1
SKILL_DIR="skills/${SKILL_NAME}"

# 建立目錄結構
mkdir -p ${SKILL_DIR}/{00-quickstart/_base,01-perspectives/_base,config,templates}

# 複製模板
cp shared/skill-structure/templates/SKILL.md.template \
   ${SKILL_DIR}/SKILL.md

cp shared/skill-structure/templates/quickstart.md.template \
   ${SKILL_DIR}/00-quickstart/_base/usage.md

cp shared/skill-structure/templates/perspectives.md.template \
   ${SKILL_DIR}/01-perspectives/_base/default-perspectives.md

cp shared/skill-structure/templates/custom-perspectives.md.template \
   ${SKILL_DIR}/01-perspectives/_base/custom-perspectives.md

cp shared/skill-structure/templates/phases.yaml.template \
   ${SKILL_DIR}/config/phases.yaml

cp shared/skill-structure/templates/quality-gates.yaml.template \
   ${SKILL_DIR}/config/quality-gates.yaml

cp shared/skill-structure/templates/meta.yaml.template \
   ${SKILL_DIR}/templates/meta.yaml.template

cp shared/skill-structure/templates/summary.md.template \
   ${SKILL_DIR}/templates/summary.md.template

echo "✅ Skill '${SKILL_NAME}' created at ${SKILL_DIR}"
echo "📝 Next steps:"
echo "   1. Edit ${SKILL_DIR}/SKILL.md (replace {{placeholders}})"
echo "   2. Edit ${SKILL_DIR}/00-quickstart/_base/usage.md"
echo "   3. Edit ${SKILL_DIR}/01-perspectives/_base/default-perspectives.md"
```

### 手動建立

1. **建立目錄**

```bash
mkdir -p skills/my-skill/{00-quickstart/_base,01-perspectives/_base,config,templates}
```

2. **複製核心模板**

```bash
cp shared/skill-structure/templates/SKILL.md.template \
   skills/my-skill/SKILL.md

cp shared/skill-structure/templates/quickstart.md.template \
   skills/my-skill/00-quickstart/_base/usage.md

cp shared/skill-structure/templates/perspectives.md.template \
   skills/my-skill/01-perspectives/_base/default-perspectives.md
```

3. **複製配置模板（可選）**

```bash
cp shared/skill-structure/templates/phases.yaml.template \
   skills/my-skill/config/phases.yaml

cp shared/skill-structure/templates/quality-gates.yaml.template \
   skills/my-skill/config/quality-gates.yaml
```

4. **複製執行模板（可選）**

```bash
cp shared/skill-structure/templates/meta.yaml.template \
   skills/my-skill/templates/meta.yaml.template

cp shared/skill-structure/templates/summary.md.template \
   skills/my-skill/templates/summary.md.template
```

## 填寫指南

### Frontmatter 佔位符

需要替換的 `{{placeholders}}`：

| 佔位符 | 說明 | 範例 |
|--------|------|------|
| `{{skill-name}}` | Skill 名稱（小寫、連字號） | `my-skill` |
| `{{Skill Name}}` | Skill 顯示名稱 | `My Skill` |
| `{{簡短的一句話描述}}` | 一句話說明 | `多 Agent 並行分析框架` |
| `{{trigger1}}`, `{{trigger2}}` | 觸發關鍵字 | `multi-analyze`, `parallel-analyze` |
| `{{agent_type}}` | Agent 類型 | `general-purpose`, `Explore`, `Plan` |
| `{{model}}` | 預設模型 | `sonnet`, `haiku`, `opus` |

### 內容佔位符

| 佔位符 | 說明 |
|--------|------|
| `{{command}}` | 命令名稱 |
| `{{STAGE}}` | 工作流階段（RESEARCH, PLAN, IMPLEMENT 等） |
| `{{type}}` | Memory 類型（research, plans, implement 等） |
| `{{id}}` | 唯一識別碼 |
| `{{perspective_X}}` | 視角 ID |
| `{{階段說明}}` | 階段的說明文字 |
| `{{機制名稱}}` | 機制的名稱 |

### 快速替換

使用編輯器的搜尋替換功能：

```bash
# 使用 sed（macOS 需要加 -i ''）
sed -i 's/{{skill-name}}/my-skill/g' skills/my-skill/SKILL.md
sed -i 's/{{Skill Name}}/My Skill/g' skills/my-skill/SKILL.md
# ... 更多替換

# 或使用互動式編輯器（VS Code、Vim 等）
```

## 模板說明

### SKILL.md.template

包含所有標準段落的完整模板：

- Frontmatter（必要和可選欄位）
- 標題與簡介
- 自動化機制
- 使用方式
- 角色配置
- 執行流程
- 關鍵機制
- CP4: Task Commit
- 品質閘門
- 輸出結構
- Agent 能力限制
- 行動日誌
- 錯誤處理
- 共用模組
- 工作流位置

### quickstart.md.template

快速開始指南模板：

- 最簡用法
- 常用模式（多種場景）
- 輸出位置
- 復用結果
- 進階技巧
- 下一步

### perspectives.md.template

視角定義模板：

- 視角總覽（ASCII 圖表）
- 每個視角的詳細說明
  - 角色定位
  - 規劃重點
  - Prompt 模板
- 視角組合策略
- 深度模式額外視角

### custom-perspectives.md.template

自訂視角指南模板：

- 使用場景
- 自訂視角結構
- 設計原則
- 視角組合建議
- 使用方式
- 視角模板庫
- 進階技巧
- 最佳實踐

### meta.yaml.template

元數據模板，記錄 Skill 執行狀態：

- 基本資訊（skill, version, workflow_id, stage）
- 執行時間（started_at, completed_at）
- 輸入參數
- 執行配置
- 輸出路徑
- 品質指標

### summary.md.template

執行摘要模板：

- 概要
- 輸入參數
- 執行過程（每個 Phase）
- 關鍵產出
- 品質指標
- 問題與解決
- 下一步
- 相關檔案
- Git Commit 資訊

### phases.yaml.template

執行階段配置模板：

- 階段定義（ID, 名稱, 說明, 依賴）
- MAP 階段（並行執行配置）
- REDUCE 階段（匯總配置）
- 錯誤處理策略
- 檢查點配置

### quality-gates.yaml.template

品質閘門配置模板：

- 閘門設定（最低分數, 是否阻擋）
- 評分標準（完整性, 品質, 一致性, 可執行性）
- 特定階段檢查
- 早期攔截規則
- 輸出配置
- 通知設定

## 檢查清單

完成模板填寫後，確認：

- [ ] 所有 `{{placeholders}}` 都已替換
- [ ] Frontmatter 欄位正確
- [ ] 命令範例可執行
- [ ] 視角配置完整
- [ ] 階段流程清晰
- [ ] 連結路徑正確
- [ ] 無語法錯誤
- [ ] 遵循命名規範

## 常見錯誤

### 1. 佔位符未替換

```markdown
❌ 錯誤
name: {{skill-name}}

✅ 正確
name: my-skill
```

### 2. 路徑錯誤

```markdown
❌ 錯誤
[link](../../../shared/config/xxx.yaml)

✅ 正確（從 skills/my-skill/SKILL.md）
[link](../../shared/config/xxx.yaml)
```

### 3. Frontmatter 格式錯誤

```yaml
❌ 錯誤
---
name: my-skill
triggers: trigger1, trigger2  # 應該是陣列
---

✅ 正確
---
name: my-skill
triggers: [trigger1, trigger2]
---
```

## 參考範例

完整的實際範例：

- [skills/research/](../../../skills/research/)
- [skills/plan/](../../../skills/plan/)
- [skills/implement/](../../../skills/implement/)

## 相關資源

- [Skill 標準規範](../STANDARD.md)
- [自動載入說明](../CLAUDE.md)
- [模型路由配置](../../config/model-routing.yaml)
- [品質閘門配置](../../quality/gates.yaml)
