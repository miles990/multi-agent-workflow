# Skill Structure Standard

> 當引用 `@shared/skill-structure` 時自動載入

## 快速參考

本目錄定義了 Claude Code Plugin 的標準 Skill 結構規範。

### 核心文件

| 檔案 | 用途 |
|------|------|
| [STANDARD.md](./STANDARD.md) | 完整的 Skill 結構規範 |
| [templates/](./templates/) | 可直接使用的模板檔案 |

### 快速開始

建立新 Skill：

```bash
# 1. 建立目錄結構
mkdir -p skills/my-skill/{00-quickstart/_base,01-perspectives/_base,config,templates}

# 2. 複製模板
cp shared/skill-structure/templates/SKILL.md.template skills/my-skill/SKILL.md
cp shared/skill-structure/templates/quickstart.md.template skills/my-skill/00-quickstart/_base/usage.md
cp shared/skill-structure/templates/perspectives.md.template skills/my-skill/01-perspectives/_base/default-perspectives.md

# 3. 填寫內容（替換 {{placeholders}}）
```

## 必須檔案

新 Skill 必須包含：

1. **SKILL.md** - 主檔案
   - Frontmatter（必要欄位：name, version, description, triggers, context, agent, allowed-tools, model）
   - 標準段落（使用方式、執行流程、輸出結構等）

2. **00-quickstart/\_base/usage.md** - 快速開始
   - 最簡用法
   - 常用模式
   - 輸出位置

3. **01-perspectives/\_base/default-perspectives.md** - 視角定義（多 Agent 模式）
   - 視角總覽
   - 每個視角的詳細說明
   - 視角組合策略

## 建議檔案

根據需求添加：

- **config/phases.yaml** - 執行階段配置
- **config/quality-gates.yaml** - 品質閘門配置
- **templates/meta.yaml.template** - 元數據模板
- **templates/summary.md.template** - 摘要模板

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

## 檔案命名規範

- 目錄：小寫、連字號 (`my-skill`)
- 檔案：小寫、連字號 (`default-perspectives.md`)
- 編號前綴：兩位數 (`00-quickstart`, `01-perspectives`)
- 模板：`.template` 後綴 (`meta.yaml.template`)

## 文檔風格

- **標題層級**：H1 主標題 → H2 主要段落 → H3 子段落
- **程式碼區塊**：指定語言 (` ```bash `, ` ```yaml `)
- **連結**：相對路徑 (`../../shared/path/to/file.md`)
- **箭頭引用**：`→ 配置：[link](path)`
- **視覺標記**：⚡ 自動 | ✅ 完成 | ❌ 禁止 | ⚠️ 注意

## 品質檢查

建立新 Skill 後檢查：

- [ ] 所有必須檔案存在
- [ ] Frontmatter 完整
- [ ] 所有連結有效
- [ ] 版本號正確
- [ ] 遵循命名規範
- [ ] 標準段落完整

## 參考範例

查看完整範例：

- **Research Skill**: [skills/research/](../../skills/research/)
- **Plan Skill**: [skills/plan/](../../skills/plan/)
- **Implement Skill**: [skills/implement/](../../skills/implement/)

## 完整規範

詳細規範請參考：[STANDARD.md](./STANDARD.md)
