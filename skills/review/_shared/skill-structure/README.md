# Skill Structure Standard

> Claude Code Plugin 標準 Skill 結構規範與模板

## 概述

本目錄提供完整的 Skill 結構規範和可直接使用的模板，確保所有 Skills 遵循一致的標準。

## 檔案結構

```
shared/skill-structure/
├── STANDARD.md              # 完整規範文件（641 行）
├── CLAUDE.md                # 自動載入說明（129 行）
├── templates/               # 模板檔案目錄
│   ├── README.md            # 模板使用指南（320 行）
│   ├── SKILL.md.template    # Skill 主檔案模板（205 行）
│   ├── quickstart.md.template         # 快速開始模板（105 行）
│   ├── perspectives.md.template       # 視角定義模板（187 行）
│   ├── custom-perspectives.md.template # 自訂視角指南（311 行）
│   ├── meta.yaml.template             # 元數據模板（42 行）
│   ├── summary.md.template            # 摘要模板（113 行）
│   ├── phases.yaml.template           # 階段配置模板（104 行）
│   └── quality-gates.yaml.template    # 品質閘門模板（112 行）
├── validate.sh              # 驗證腳本
└── README.md                # 本檔案

總計：2,269 行文檔和模板
```

## 快速開始

### 1. 查看規範

```bash
# 完整規範
cat shared/skill-structure/STANDARD.md

# 快速參考
cat shared/skill-structure/CLAUDE.md
```

### 2. 建立新 Skill

```bash
# 方式 1: 使用腳本（推薦）
./scripts/create-skill.sh my-skill

# 方式 2: 手動建立
mkdir -p skills/my-skill/{00-quickstart/_base,01-perspectives/_base,config,templates}
cp shared/skill-structure/templates/SKILL.md.template skills/my-skill/SKILL.md
cp shared/skill-structure/templates/quickstart.md.template skills/my-skill/00-quickstart/_base/usage.md
# ... 複製其他模板
```

### 3. 填寫模板

替換所有 `{{placeholders}}`：

```bash
# 使用編輯器的搜尋替換功能
# 或使用 sed
sed -i 's/{{skill-name}}/my-skill/g' skills/my-skill/SKILL.md
sed -i 's/{{Skill Name}}/My Skill/g' skills/my-skill/SKILL.md
# ...
```

### 4. 驗證結構

```bash
# 驗證 skill-structure 本身
./shared/skill-structure/validate.sh

# 驗證新建的 Skill（TODO: 建立驗證腳本）
# ./scripts/validate-skill.sh my-skill
```

## 核心文件

### STANDARD.md

完整的 Skill 結構規範，包含：

- **目錄結構**：必須/建議/可選檔案
- **Frontmatter 規範**：必要/可選欄位
- **標準段落**：13 個標準段落定義
- **文檔風格**：命名規範、Markdown 風格
- **版本控制**：語義化版本、變更記錄
- **整合規範**：Hooks、共用模組、Memory 存檔
- **檢查清單**：建立新 Skill 的檢查項目

### CLAUDE.md

自動載入說明，當引用 `@shared/skill-structure` 時顯示：

- 快速參考
- 核心文件索引
- 快速開始步驟
- 必須檔案清單
- Frontmatter 範例
- 品質檢查清單

## 模板說明

### 核心模板

| 模板 | 行數 | 用途 |
|------|------|------|
| SKILL.md.template | 205 | Skill 主檔案，包含所有標準段落 |
| quickstart.md.template | 105 | 快速開始指南 |
| perspectives.md.template | 187 | 視角定義（多 Agent 模式） |
| custom-perspectives.md.template | 311 | 自訂視角指南 |

### 配置模板

| 模板 | 行數 | 用途 |
|------|------|------|
| meta.yaml.template | 42 | Skill 執行元數據 |
| summary.md.template | 113 | 執行結果摘要 |
| phases.yaml.template | 104 | 執行階段配置 |
| quality-gates.yaml.template | 112 | 品質閘門配置 |

詳細說明請參考：[templates/README.md](./templates/README.md)

## 標準 Skill 結構

遵循此規範的 Skill 應包含：

```
skills/my-skill/
├── SKILL.md                    # 主檔案（必須）
├── 00-quickstart/              # 快速開始（必須）
│   └── _base/
│       └── usage.md
├── 01-perspectives/            # 視角定義（多 Agent 必須）
│   └── _base/
│       ├── default-perspectives.md
│       └── custom-perspectives.md
├── config/                     # 配置檔案（建議）
│   ├── phases.yaml
│   └── quality-gates.yaml
└── templates/                  # 模板檔案（建議）
    ├── meta.yaml.template
    └── summary.md.template
```

## Frontmatter 範例

```yaml
---
name: my-skill
version: 1.0.0
description: 簡短的一句話描述
triggers: [trigger1, trigger2]
context: fork
agent: general-purpose
allowed-tools: [Read, Write, Edit, Bash, Grep, Glob]
model: sonnet
hooks: true
---
```

## 標準段落

SKILL.md 應包含（按順序）：

1. 標題與簡介
2. 自動化機制（如使用 hooks）
3. 使用方式
4. 角色配置（多 Agent）
5. 執行流程
6. 關鍵機制（TDD、品質閘門等）
7. CP4: Task Commit
8. 品質閘門
9. 輸出結構
10. Agent 能力限制（多 Agent）
11. 行動日誌
12. 共用模組
13. 工作流位置

## 使用場景

### 建立新 Skill

參考 [templates/README.md](./templates/README.md) 中的詳細步驟。

### 重構現有 Skill

1. 對照 STANDARD.md 檢查缺少的部分
2. 使用模板補充缺少的檔案
3. 更新 frontmatter 和標準段落
4. 確保連結正確

### 自訂引用

在其他文件中引用時，Claude Code 會自動載入 CLAUDE.md：

```markdown
參考 @shared/skill-structure 了解 Skill 結構標準
```

## 驗證

### 自動驗證

```bash
# 驗證 skill-structure 本身
./shared/skill-structure/validate.sh
```

### 手動檢查清單

- [ ] 所有必須檔案存在
- [ ] Frontmatter 包含所有必要欄位
- [ ] 所有 `{{placeholders}}` 已替換
- [ ] 所有連結有效
- [ ] 版本號正確
- [ ] 遵循命名規範
- [ ] 標準段落完整

## 參考範例

完整的實際範例：

- [skills/research/](../../skills/research/) - Research Skill（3.2.0）
- [skills/plan/](../../skills/plan/) - Plan Skill（3.2.0）
- [skills/implement/](../../skills/implement/) - Implement Skill（3.1.0）

## 相關資源

| 資源 | 路徑 | 說明 |
|------|------|------|
| 模型路由 | [shared/config/model-routing.yaml](../config/model-routing.yaml) | Agent 模型配置 |
| 品質閘門 | [shared/quality/gates.yaml](../quality/gates.yaml) | 品質標準 |
| Map 協調 | [shared/coordination/map-phase.md](../coordination/map-phase.md) | 並行執行 |
| Reduce 協調 | [shared/coordination/reduce-phase.md](../coordination/reduce-phase.md) | 匯總整合 |
| Commit 協議 | [shared/git/commit-protocol.md](../git/commit-protocol.md) | Git 提交規範 |

## 貢獻

### 更新規範

1. 修改 STANDARD.md
2. 同步更新 CLAUDE.md（快速參考）
3. 更新相關模板
4. 執行驗證：`./validate.sh`
5. 提交變更

### 新增模板

1. 在 `templates/` 目錄建立新模板
2. 更新 `templates/README.md`
3. 更新本檔案的模板清單
4. 更新驗證腳本
5. 提交變更

## 版本歷史

### v1.0.0 (2026-02-01)

- 初始版本
- 完整規範文件（641 行）
- 9 個模板檔案（1,499 行）
- 自動載入說明
- 驗證腳本

## 授權

本規範和模板遵循專案的整體授權條款。

---

**提示**：引用 `@shared/skill-structure` 時會自動載入 CLAUDE.md 快速參考。
