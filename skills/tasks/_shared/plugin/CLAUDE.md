# Plugin 配置模組

> 管理 Plugin 開發工作流的共用配置

## 配置檔案

| 檔案 | 用途 |
|------|------|
| `config.yaml` | 主配置：元數據、同步、監控、版本、發布 |
| `cache-policy.yaml` | 快取策略：位置、保留、同步模式、驗證 |
| `version-strategy.yaml` | 版本策略：語義化版本、相容性、棄用 |

## 使用方式

### 在 Python 中載入配置

```python
import yaml
from pathlib import Path

config_dir = Path(__file__).parent / "shared" / "plugin"

# 載入主配置
with open(config_dir / "config.yaml") as f:
    config = yaml.safe_load(f)

# 取得快取基礎路徑
cache_base = config["cache"]["base_path"]
```

### 在 Shell 腳本中使用

```bash
# 使用 yq 解析 YAML
CACHE_BASE=$(yq '.cache.base_path' shared/plugin/config.yaml)
DEBOUNCE_MS=$(yq '.watch.debounce_ms' shared/plugin/config.yaml)
```

## 配置優先順序

1. 環境變數 (最高)
2. `.plugin-dev/*.json` (專案級)
3. `shared/plugin/*.yaml` (全域預設)

## 環境變數覆蓋

| 變數 | 對應配置 |
|------|----------|
| `PLUGIN_CACHE_BASE` | `cache.base_path` |
| `PLUGIN_SYNC_MODE` | `cache.sync_mode` |
| `PLUGIN_WATCH_DEBOUNCE` | `watch.debounce_ms` |

## 擴展配置

新增配置時：
1. 在對應 YAML 中添加
2. 更新 Python 模組讀取
3. 更新此文檔

## 相關模組

- `cli/plugin/cache.py` - 使用 cache-policy.yaml
- `cli/plugin/version.py` - 使用 version-strategy.yaml
- `cli/plugin/dev.py` - 使用 config.yaml 的 watch 設定
- `cli/plugin/release.py` - 使用 config.yaml 的 release 設定
