"""設定管理

統一讀取和快取設定，提供預設值。
支援 OCP（Open/Closed Principle）- 新增 commit type 不需修改代碼。
"""

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


class ConfigManager:
    """設定管理 - 統一讀取和快取設定

    統一管理：
    - Co-Author 常數（消除 16+ 次重複）
    - Commit type 映射
    - 排除模式
    - Commit 設定

    Example:
        config = ConfigManager(Path("/my/project"))
        settings = config.get_commit_settings()
        co_author = config.get_co_author()
    """

    # Co-Author 常數（統一定義，消除重複）
    CO_AUTHOR = "Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"

    # 預設 commit type 映射（支援 OCP - 可擴展無需改代碼）
    DEFAULT_COMMIT_TYPES: Dict[str, str] = {
        "research": "docs",
        "plans": "feat",
        "tasks": "feat",
        "implement": "feat",
        "review": "docs",
        "verify": "test",
        "refactor": "refactor",
    }

    # 預設排除模式
    DEFAULT_EXCLUDE_PATTERNS: List[str] = [
        "*.pyc",
        "__pycache__/",
        ".pytest_cache/",
        "*.egg-info/",
        ".DS_Store",
        "*.log",
        ".env*",
        "node_modules/",
        "dist/",
        ".venv/",
    ]

    def __init__(self, project_dir: Path):
        """初始化

        Args:
            project_dir: 專案根目錄
        """
        self.project_dir = Path(project_dir)

    @lru_cache(maxsize=1)
    def get_commit_settings(self) -> Dict[str, Any]:
        """讀取 commit 設定（帶快取）

        從 shared/config/commit-settings.yaml 讀取設定，
        若檔案不存在或無法解析則返回預設值。

        Returns:
            commit 設定字典
        """
        default: Dict[str, Any] = {
            "enabled": True,
            "include_memory": False,
            "include_logs": False,
            "exclude_patterns": self.DEFAULT_EXCLUDE_PATTERNS.copy(),
        }

        if yaml is None:
            return default

        config_path = self.project_dir / "shared" / "config" / "commit-settings.yaml"
        if not config_path.exists():
            return default

        try:
            with open(config_path) as f:
                config = yaml.safe_load(f)
                if config and "task_commit" in config:
                    return config["task_commit"]
                return default
        except Exception:
            return default

    def get_commit_type(self, memory_type: str) -> str:
        """取得 memory type 對應的 commit type

        優先從設定檔讀取，若無則使用預設映射。
        支援 OCP - 新增類型只需在設定檔添加。

        Args:
            memory_type: memory 類型（如 "research", "plans"）

        Returns:
            commit type（如 "docs", "feat"）
        """
        # 嘗試從設定檔讀取
        if yaml:
            config_path = self.project_dir / "shared" / "config" / "commit-settings.yaml"
            if config_path.exists():
                try:
                    with open(config_path) as f:
                        config = yaml.safe_load(f)
                        if config:
                            type_mapping = config.get("commit_types", {})
                            if memory_type in type_mapping:
                                return type_mapping[memory_type]
                except Exception:
                    pass

        return self.DEFAULT_COMMIT_TYPES.get(memory_type, "chore")

    def get_co_author(self) -> str:
        """取得 Co-Author 字串

        統一的 Co-Author 簽名，消除之前 16+ 次的重複定義。

        Returns:
            Co-Author 字串
        """
        return self.CO_AUTHOR

    def get_exclude_patterns(self) -> List[str]:
        """取得排除模式列表

        Returns:
            排除模式列表
        """
        settings = self.get_commit_settings()
        return settings.get("exclude_patterns", self.DEFAULT_EXCLUDE_PATTERNS.copy())
