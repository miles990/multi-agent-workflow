"""
DAG 驗證器 - 驗證任務依賴圖的正確性

檢查項目：
1. 依賴指向不存在的任務
2. 循環依賴
3. TDD 對應（TEST-* 是否 block T-F-*）
4. 孤立任務
"""

from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple


class DAGValidationResult:
    """DAG 驗證結果"""

    def __init__(self):
        self.valid = True
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.stats: Dict = {}

    def add_error(self, message: str) -> None:
        self.errors.append(message)
        self.valid = False

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)


class DAGValidator:
    """DAG 驗證器"""

    def validate(self, tasks: List[Dict]) -> DAGValidationResult:
        """
        驗證任務 DAG

        Args:
            tasks: 任務列表

        Returns:
            DAGValidationResult 物件
        """
        result = DAGValidationResult()

        if not tasks:
            result.add_error("任務列表為空")
            return result

        # 建立資料結構
        graph: Dict[str, List[str]] = defaultdict(list)
        all_ids: Set[str] = set()
        task_map: Dict[str, Dict] = {}

        for task in tasks:
            task_id = task.get("id", "")
            if not task_id:
                continue

            all_ids.add(task_id)
            task_map[task_id] = task

            deps = self._get_dependencies(task)
            for dep in deps:
                graph[dep].append(task_id)

        result.stats["total_tasks"] = len(all_ids)

        # 1. 檢查依賴指向不存在的任務
        self._check_missing_dependencies(tasks, all_ids, result)

        # 2. 檢查循環依賴
        self._check_cycles(all_ids, graph, result)

        # 3. 檢查 TDD 對應
        self._check_tdd_mapping(tasks, all_ids, result)

        # 4. 檢查孤立任務
        self._check_orphans(tasks, all_ids, result)

        return result

    def _get_dependencies(self, task: Dict) -> List[str]:
        """取得任務的依賴列表"""
        deps = task.get("depends_on", []) or task.get("blockedBy", []) or []
        if isinstance(deps, str):
            deps = [deps]
        return deps

    def _check_missing_dependencies(
        self,
        tasks: List[Dict],
        all_ids: Set[str],
        result: DAGValidationResult,
    ) -> None:
        """檢查依賴指向不存在的任務"""
        for task in tasks:
            task_id = task.get("id", "")
            deps = self._get_dependencies(task)

            for dep in deps:
                if dep not in all_ids:
                    result.add_error(f"任務 {task_id} 依賴不存在的任務: {dep}")

    def _check_cycles(
        self,
        all_ids: Set[str],
        graph: Dict[str, List[str]],
        result: DAGValidationResult,
    ) -> None:
        """檢查循環依賴"""
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def find_cycle(
            node: str,
            path: List[str],
        ) -> Optional[List[str]]:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    cycle = find_cycle(neighbor, path)
                    if cycle:
                        return cycle
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:] + [neighbor]

            path.pop()
            rec_stack.remove(node)
            return None

        for task_id in all_ids:
            if task_id not in visited:
                cycle = find_cycle(task_id, [])
                if cycle:
                    cycle_str = " → ".join(cycle)
                    result.add_error(f"發現循環依賴: {cycle_str}")

    def _check_tdd_mapping(
        self,
        tasks: List[Dict],
        all_ids: Set[str],
        result: DAGValidationResult,
    ) -> None:
        """檢查 TDD 對應"""
        for task in tasks:
            task_id = task.get("id", "")

            # 檢查 T-F-* 是否有對應的 TEST-*
            if task_id.startswith("T-F-"):
                test_id = task_id.replace("T-F-", "TEST-")

                if test_id in all_ids:
                    # 檢查 TEST-* 是否在 depends_on 中
                    deps = self._get_dependencies(task)
                    if test_id not in deps:
                        result.add_warning(
                            f"TDD: {task_id} 應該依賴 {test_id}"
                        )
                else:
                    result.add_warning(
                        f"TDD: {task_id} 缺少對應的測試任務 {test_id}"
                    )

    def _check_orphans(
        self,
        tasks: List[Dict],
        all_ids: Set[str],
        result: DAGValidationResult,
    ) -> None:
        """檢查孤立任務"""
        in_degree: Dict[str, int] = defaultdict(int)
        out_degree: Dict[str, int] = defaultdict(int)

        for task in tasks:
            task_id = task.get("id", "")
            deps = self._get_dependencies(task)

            out_degree[task_id] = 0  # 初始化
            for dep in deps:
                in_degree[task_id] += 1
                out_degree[dep] += 1

        orphans = [
            tid
            for tid in all_ids
            if in_degree[tid] == 0
            and out_degree[tid] == 0
            and not tid.startswith("SETUP-")
            and not tid.startswith("INIT-")
        ]

        # 只有一個任務不算孤立
        if orphans and len(orphans) < len(all_ids):
            for orphan in orphans:
                result.add_warning(f"孤立任務（無入無出）: {orphan}")

        result.stats["orphan_count"] = len(orphans)


def validate_dag(tasks: List[Dict]) -> DAGValidationResult:
    """快速驗證 DAG"""
    validator = DAGValidator()
    return validator.validate(tasks)


def is_dag_valid(tasks: List[Dict]) -> bool:
    """檢查 DAG 是否有效"""
    result = validate_dag(tasks)
    return result.valid
