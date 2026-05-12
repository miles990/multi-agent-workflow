"""
Memory 讀寫模組 - 管理 .claude/memory/ 目錄結構

負責：
- 工作流目錄建立與管理
- YAML/JSON 檔案讀寫
- 路徑解析與驗證
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml


class MemoryManager:
    """Memory 目錄管理器"""

    def __init__(self, base_path: Optional[str] = None):
        """
        初始化 Memory 管理器

        Args:
            base_path: Memory 根目錄，預設為 .claude/memory/
        """
        if base_path:
            self.base_path = Path(base_path)
        else:
            self.base_path = Path(".claude/memory")

        self._ensure_base_dirs()

    def _ensure_base_dirs(self) -> None:
        """確保基礎目錄存在"""
        dirs = [
            self.base_path,
            self.base_path / "workflows",
            self.base_path / "research",
            self.base_path / "plans",
            self.base_path / "tasks",
            self.base_path / "implement",
            self.base_path / "review",
            self.base_path / "verify",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    # ─────────────────────────────────────────────────────────────────────────
    # 工作流管理
    # ─────────────────────────────────────────────────────────────────────────

    def create_workflow_dir(
        self,
        workflow_id: str,
        topic: str,
        config: Optional[Dict] = None,
    ) -> Path:
        """
        建立工作流目錄結構

        Args:
            workflow_id: 工作流 ID
            topic: 工作流主題
            config: 額外配置

        Returns:
            工作流目錄路徑
        """
        workflow_dir = self.base_path / "workflows" / workflow_id
        workflow_dir.mkdir(parents=True, exist_ok=True)

        # 建立子目錄
        subdirs = ["stages", "agents", "logs", "exports"]
        for subdir in subdirs:
            (workflow_dir / subdir).mkdir(exist_ok=True)

        # 建立 meta.yaml
        meta = {
            "id": workflow_id,
            "topic": topic,
            "status": "initialized",
            "created_at": datetime.now().isoformat(),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "config": config or {},
            "current_stage": None,
            "stages": {},
        }
        self.write_yaml(workflow_dir / "meta.yaml", meta)

        return workflow_dir

    def get_workflow_dir(self, workflow_id: str) -> Optional[Path]:
        """取得工作流目錄"""
        workflow_dir = self.base_path / "workflows" / workflow_id
        if workflow_dir.exists():
            return workflow_dir
        return None

    def list_workflows(self, limit: int = 10) -> List[Dict]:
        """列出所有工作流"""
        workflows_dir = self.base_path / "workflows"
        if not workflows_dir.exists():
            return []

        workflows = []
        for wf_dir in workflows_dir.iterdir():
            if wf_dir.is_dir():
                meta_file = wf_dir / "meta.yaml"
                if meta_file.exists():
                    meta = self.read_yaml(meta_file)
                    if meta:
                        workflows.append(meta)

        # 按日期排序
        workflows.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return workflows[:limit]

    def get_active_workflow(self) -> Optional[Dict]:
        """取得當前活動的工作流"""
        workflows = self.list_workflows()
        for wf in workflows:
            if wf.get("status") in ["running", "in_progress", "initialized"]:
                return wf
        return workflows[0] if workflows else None

    # ─────────────────────────────────────────────────────────────────────────
    # 階段目錄管理
    # ─────────────────────────────────────────────────────────────────────────

    def create_stage_dir(
        self,
        workflow_id: str,
        stage: str,
    ) -> Path:
        """
        建立階段目錄

        Args:
            workflow_id: 工作流 ID
            stage: 階段名稱

        Returns:
            階段目錄路徑
        """
        workflow_dir = self.get_workflow_dir(workflow_id)
        if not workflow_dir:
            raise FileNotFoundError(f"Workflow not found: {workflow_id}")

        stage_dir = workflow_dir / "stages" / stage.lower()
        stage_dir.mkdir(parents=True, exist_ok=True)

        # 建立子目錄
        (stage_dir / "perspectives").mkdir(exist_ok=True)
        (stage_dir / "summaries").mkdir(exist_ok=True)

        return stage_dir

    def get_stage_dir(self, workflow_id: str, stage: str) -> Optional[Path]:
        """取得階段目錄"""
        workflow_dir = self.get_workflow_dir(workflow_id)
        if not workflow_dir:
            return None

        stage_dir = workflow_dir / "stages" / stage.lower()
        if stage_dir.exists():
            return stage_dir
        return None

    # ─────────────────────────────────────────────────────────────────────────
    # 檔案讀寫
    # ─────────────────────────────────────────────────────────────────────────

    def read_yaml(self, path: Union[str, Path]) -> Optional[Dict]:
        """讀取 YAML 檔案"""
        path = Path(path)
        if not path.exists():
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return None

    def write_yaml(self, path: Union[str, Path], data: Dict) -> bool:
        """寫入 YAML 檔案"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(
                    data,
                    f,
                    allow_unicode=True,
                    default_flow_style=False,
                    sort_keys=False,
                )
            return True
        except Exception:
            return False

    def read_json(self, path: Union[str, Path]) -> Optional[Dict]:
        """讀取 JSON 檔案"""
        path = Path(path)
        if not path.exists():
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def write_json(self, path: Union[str, Path], data: Dict) -> bool:
        """寫入 JSON 檔案"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    def read_text(self, path: Union[str, Path]) -> Optional[str]:
        """讀取文字檔案"""
        path = Path(path)
        if not path.exists():
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return None

    def write_text(self, path: Union[str, Path], content: str) -> bool:
        """寫入文字檔案"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception:
            return False

    def append_jsonl(self, path: Union[str, Path], data: Dict) -> bool:
        """追加 JSONL 記錄"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(data, ensure_ascii=False) + "\n")
            return True
        except Exception:
            return False

    def read_jsonl(self, path: Union[str, Path]) -> List[Dict]:
        """讀取 JSONL 檔案"""
        path = Path(path)
        if not path.exists():
            return []

        records = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        records.append(json.loads(line))
        except Exception:
            pass

        return records

    # ─────────────────────────────────────────────────────────────────────────
    # 工作流狀態更新
    # ─────────────────────────────────────────────────────────────────────────

    def update_workflow_meta(
        self,
        workflow_id: str,
        updates: Dict[str, Any],
    ) -> bool:
        """更新工作流 meta.yaml"""
        workflow_dir = self.get_workflow_dir(workflow_id)
        if not workflow_dir:
            return False

        meta_file = workflow_dir / "meta.yaml"
        meta = self.read_yaml(meta_file) or {}
        meta.update(updates)
        meta["updated_at"] = datetime.now().isoformat()

        return self.write_yaml(meta_file, meta)

    def update_stage_status(
        self,
        workflow_id: str,
        stage: str,
        status: str,
        details: Optional[Dict] = None,
    ) -> bool:
        """更新階段狀態"""
        workflow_dir = self.get_workflow_dir(workflow_id)
        if not workflow_dir:
            return False

        meta_file = workflow_dir / "meta.yaml"
        meta = self.read_yaml(meta_file) or {}

        if "stages" not in meta:
            meta["stages"] = {}

        meta["stages"][stage.lower()] = {
            "status": status,
            "updated_at": datetime.now().isoformat(),
            **(details or {}),
        }

        if status == "running":
            meta["current_stage"] = stage.upper()
            meta["status"] = "running"

        return self.write_yaml(meta_file, meta)


# 全域實例
_memory: Optional[MemoryManager] = None


def get_memory(base_path: Optional[str] = None) -> MemoryManager:
    """取得全域 Memory 管理器實例"""
    global _memory
    if _memory is None or base_path:
        _memory = MemoryManager(base_path)
    return _memory
