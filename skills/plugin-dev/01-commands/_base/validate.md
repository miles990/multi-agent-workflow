# /plugin-dev validate

> 驗證 Plugin 結構和版本一致性

## 格式

```bash
/plugin-dev validate [--strict] [--fix]
```

## 參數

| 參數 | 說明 |
|------|------|
| `--strict` | 嚴格模式（警告也視為錯誤） |
| `--fix` | 自動修復可修復的問題 |

## 實作路徑

```
Skill → Bash: python -m cli.plugin.release validate [options]
     → ReleaseCommands.validate()
     → ValidationResult
```

## 驗證項目

### 必要檢查

| 項目 | 說明 |
|------|------|
| plugin.json | 必須存在且 JSON 格式有效 |
| skills/ | 目錄必須存在 |
| SKILL.md | 至少一個 SKILL.md 檔案 |

### 版本一致性

檢查以下檔案的版本是否一致：
- `plugin.json`
- `marketplace.json`
- `CLAUDE.md`（標題中的版本）

### 結構檢查

| 項目 | 說明 |
|------|------|
| frontmatter | 每個 SKILL.md 必須有有效的 frontmatter |
| required fields | name, description, version 必須存在 |
| triggers | 至少定義一個觸發器 |

## 範例

### 基本驗證

```bash
/plugin-dev validate
```

輸出：
```
✓ 驗證通過

檢查結果:
  ✓ plugin.json 有效
  ✓ skills/ 目錄存在
  ✓ 找到 10 個 SKILL.md
  ✓ 版本一致: 2.4.0
  ✓ 所有 frontmatter 有效
```

### 發現問題

```bash
/plugin-dev validate
```

輸出：
```
⚠ 發現 2 個問題

問題:
  1. [WARNING] marketplace.json 版本 (2.3.0) 與 plugin.json (2.4.0) 不一致
  2. [WARNING] skills/test/SKILL.md 缺少 description 欄位

建議: 執行 /plugin-dev validate --fix 自動修復
```

### 嚴格模式

```bash
/plugin-dev validate --strict
```

警告也視為錯誤，返回非零退出碼。

### 自動修復

```bash
/plugin-dev validate --fix
```

輸出：
```
✓ 已修復 2 個問題

修復:
  ✓ 已更新 marketplace.json 版本為 2.4.0
  ✓ 已為 skills/test/SKILL.md 添加 description

請檢查變更並提交
```

## 錯誤處理

### plugin.json 不存在

```
✗ 驗證失敗

錯誤: plugin.json 不存在

修復建議:
  1. 確認在正確的專案目錄
  2. 建立 plugin.json:
     {
       "name": "my-plugin",
       "version": "1.0.0"
     }
```

### 無效的 JSON 格式

```
✗ 驗證失敗

錯誤: plugin.json JSON 格式無效
  行 5: 預期 ',' 或 '}'

修復建議:
  1. 檢查 JSON 語法
  2. 使用 JSON 驗證工具
```

## 相關命令

- `/plugin-dev status` - 查看當前狀態
- `/plugin-dev version check` - 檢查版本一致性
