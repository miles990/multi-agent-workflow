# plugin-dev 快速開始

> 30 秒上手 Plugin 開發工作流

## 基本使用

### 1. 同步到快取

將源碼同步到 Claude Code 快取：

```bash
/plugin-dev sync
```

### 2. 驗證結構

檢查 Plugin 結構是否正確：

```bash
/plugin-dev validate
```

### 3. 查看狀態

查看快取和版本資訊：

```bash
/plugin-dev status
```

## 開發模式

### 熱載入

啟動監控模式，檔案變更自動同步：

```bash
/plugin-dev watch
```

按 `Ctrl+C` 停止監控。

### 背景執行

在背景執行監控：

```bash
/plugin-dev watch --background
```

## 發布流程

### 發布 patch 版本

```bash
/plugin-dev release patch
```

### 預覽發布

```bash
/plugin-dev release minor --dry-run
```

### 從中斷點恢復

```bash
/plugin-dev release --resume
```

## 常用參數

| 參數 | 說明 |
|------|------|
| `--help, -h` | 顯示命令幫助 |
| `--verbose, -v` | 詳細輸出 |
| `--dry-run` | 預覽模式 |
| `--yes, -y` | 跳過確認 |
| `--json` | JSON 格式輸出 |

## 故障排除

### 快取不存在

```bash
# 首次使用，執行同步
/plugin-dev sync
```

### 版本不一致

```bash
# 自動修復
/plugin-dev validate --fix
```

### 修改後 Claude Code 沒有更新

```bash
# 重新同步
/plugin-dev sync --force
# 然後重啟 Claude Code
```

## 更多幫助

```bash
/plugin-dev help
/plugin-dev <command> --help
```

---

完整文檔：[SKILL.md](../../SKILL.md)
