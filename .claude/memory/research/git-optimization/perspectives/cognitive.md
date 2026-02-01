# 認知科學視角：Git 操作優化分析

> 從認知負擔、設計原則、可維護性角度分析 multi-agent-workflow plugin 的 Git 使用

## 執行摘要

當前 Git 操作分散在多個 hook 中，存在明顯的 DRY 違反和認知負擔問題。主要發現：

- **5 處重複的 `_get_current_workflow_id()` 函數**（149-161 行完全相同）
- **3 種不同的 commit message 生成邏輯**，缺乏統一抽象
- **7 處 `subprocess.run(["git", ...])` 呼叫**，缺乏錯誤處理抽象
- **認知負擔高**：新開發者需要理解 5 個 hook 檔案才能掌握 Git 邏輯

建議建立統一的 `GitCommitService` 抽象層，減少 60% 重複代碼，降低認知負擔。

---

## 1. DRY 違反清單

### 1.1 重複函數：`_get_current_workflow_id()`

**位置**：
- `post_task.py:149-161` (13 行)
- `subagent_stop.py:180-192` (13 行)
- `pre_task.py:64-76` (13 行)
- `post_write.py:45-57` (13 行)
- `subagent_start.py:65-77` (13 行)

**代碼**：
```python
def _get_current_workflow_id(project_dir: str) -> str:
    """從最近的 workflow 目錄取得 ID"""
    workflow_dir = Path(project_dir) / ".claude" / "workflow"
    if workflow_dir.exists():
        for d in sorted(workflow_dir.iterdir(), reverse=True):
            if d.is_dir() and (d / "current.json").exists():
                try:
                    with open(d / "current.json") as f:
                        state = json.load(f)
                        return state.get("workflow_id", d.name)
                except:
                    pass
    return ""
```

**問題**：
- 完全相同的邏輯重複 5 次
- 總計 65 行重複代碼
- 修改時需要同步更新 5 個檔案
- 錯誤處理（裸 `except:`）在 5 處重複

**認知成本**：
- 新開發者需要讀 5 遍相同邏輯才能確認「真的一模一樣」
- 修復 bug 時容易遺漏某個檔案

---

### 1.2 重複邏輯：Git Status 檢查

**模式 A - 檢查目錄變更** (3 處):

```python
# post_task.py:77-81
cmd = ["git", "status", "--porcelain", "--"] + pathspecs
result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_dir)
if not result.stdout.strip():
    return  # 無變更

# subagent_stop.py:58-66
result = subprocess.run(
    ["git", "status", "--porcelain", str(memory_dir)],
    capture_output=True, text=True, cwd=project_dir,
)
if not result.stdout.strip():
    return  # 沒有變更

# templates/workflow_hooks.py:37-42
result = subprocess.run(
    ["git", "status", "--porcelain"],
    capture_output=True, text=True, cwd=project_dir
)
if not result.stdout.strip():
    return False
```

**問題**：
- 相似但不完全相同的實作（參數差異）
- 缺乏統一的「檢查變更」抽象
- 錯誤處理不一致（有些檢查 returncode，有些不檢查）

---

### 1.3 重複邏輯：Git Add + Commit

**模式 B - Stage + Commit 流程** (3 處):

```python
# post_task.py:84-99
cmd = ["git", "add", "--"] + pathspecs
subprocess.run(cmd, cwd=project_dir, capture_output=True)

commit_message = f"""chore(task): {task_summary}

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"""

subprocess.run(
    ["git", "commit", "-m", commit_message],
    cwd=project_dir, capture_output=True,
)

# subagent_stop.py:109-156 (類似但更複雜)
subprocess.run(["git", "add", memory_dir], cwd=project_dir, capture_output=True)
commit_message = f"""{commit_type}({memory_type}): complete {topic}
...
Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"""
result = subprocess.run(["git", "commit", "-m", commit_message], ...)

# templates/workflow_hooks.py:46-64
subprocess.run(["git", "add", "-A"], cwd=project_dir, capture_output=True)
full_msg = f"{message}\n\nCo-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
result = subprocess.run(["git", "commit", "-m", full_msg], cwd=project_dir, capture_output=True)
```

**問題**：
- Stage + Commit 模式重複 3 次，但細節不同
- Co-Author 字串重複 7+ 次（硬編碼）
- 錯誤處理不一致（有些檢查 returncode，有些不檢查）

---

### 1.4 重複資料：Commit Type 映射

**位置**：
- `subagent_stop.py:117-125` - hardcoded dict
- `shared/git/commit-protocol.md:37-46` - 文檔中的表格
- `skills/memory-commit/SKILL.md:36-44` - 另一份表格

**代碼**：
```python
# subagent_stop.py
commit_types = {
    "research": "docs",
    "plans": "feat",
    "tasks": "feat",
    "implement": "feat",
    "review": "docs",
    "verify": "test",
}
```

**問題**：
- 映射邏輯散落在代碼 + 2 份文檔中
- 新增 memory type 時需要同步更新 3 個地方
- 缺乏 single source of truth

---

### 1.5 重複字串：Co-Author 簽名

**位置**：出現 16+ 次

```python
"Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

**檔案**：
- `post_task.py:92`
- `subagent_stop.py:148`
- `templates/workflow_hooks.py:59`
- `shared/git/commit-protocol.md` (5 次)
- `skills/memory-commit/SKILL.md` (2 次)
- 其他文檔...

**問題**：
- Magic string 散落各處
- 修改 Co-Author（如版本升級）需要全局搜尋替換
- 容易出現拼寫不一致

---

## 2. SOLID 原則評估

### 2.1 Single Responsibility Principle (SRP) - ⚠️ 部分違反

**評分**: 6/10

**良好實踐**：
- ✅ `update_state.py` - 專注狀態管理
- ✅ `log_action.py` - 專注動作記錄
- ✅ 各 hook 檔案職責明確（pre_task, post_task, subagent_stop）

**違反之處**：
- ❌ `post_task.py` - 混合了「狀態更新」「動作記錄」「Git commit」三個職責
- ❌ `subagent_stop.py` - 混合了「記錄」「Git 操作」「commit message 生成」
- ❌ `templates/workflow_hooks.py` - 混合了「commit」「測試運行」「驗證」

**影響**：
- 單個檔案過長（`subagent_stop.py` 196 行）
- 測試困難（需要 mock Git + 狀態系統）
- 修改一個功能可能影響其他功能

---

### 2.2 Open/Closed Principle (OCP) - ❌ 明顯違反

**評分**: 3/10

**問題場景**：

**場景 1 - 新增 commit type**
```python
# 需要修改 subagent_stop.py
commit_types = {
    "research": "docs",
    "plans": "feat",
    "tasks": "feat",
    "implement": "feat",
    "review": "docs",
    "verify": "test",
    # 新增 → 需要修改現有代碼
}
```

**場景 2 - 新增 pathspec 排除規則**
```python
# 需要修改 post_task.py
if not settings.get("include_memory", False):
    pathspecs.append(":!.claude/memory/")
# 新增規則 → 需要修改現有代碼
```

**場景 3 - 自訂 commit message 格式**
- 目前硬編碼在每個 hook 中
- 無法通過配置擴展

**應有設計**：
```python
# 應該支援策略模式
class CommitMessageFormatter:
    def format(self, type, scope, description, **kwargs): ...

class ConventionalCommitsFormatter(CommitMessageFormatter):
    def format(self, type, scope, description, **kwargs):
        return f"{type}({scope}): {description}\n\nCo-Authored-By: ..."

# 可擴展但不修改
formatters = {
    "conventional": ConventionalCommitsFormatter(),
    "simple": SimpleFormatter(),
}
```

---

### 2.3 Liskov Substitution Principle (LSP) - ✅ 符合

**評分**: 8/10

**良好實踐**：
- Hook 函數簽名一致（都接收 `input_data: dict`）
- 可以替換不同的 hook 實作
- 輸入輸出契約明確

**小問題**：
- `_get_current_workflow_id()` 在不同檔案中雖然相同，但理論上可以有不同實作
- 缺乏明確的介面定義（Python 無編譯時檢查）

---

### 2.4 Interface Segregation Principle (ISP) - ⚠️ 部分違反

**評分**: 5/10

**問題**：

**臃腫的 `subprocess.run()` 參數**
```python
# 有些需要 capture_output
subprocess.run(..., capture_output=True, text=True, cwd=project_dir)

# 有些不需要
subprocess.run(..., cwd=project_dir, capture_output=True)

# 有些需要檢查 returncode
result = subprocess.run(...)
if result.returncode == 0:
    ...
```

**應有設計**：
```python
# 隔離不同需求的介面
class GitCommand:
    def check_changes(self, paths) -> bool:
        """只需要知道有沒有變更"""
        
    def stage_files(self, paths) -> None:
        """只需要 stage，不需要輸出"""
        
    def commit(self, message) -> CommitResult:
        """需要完整結果"""
```

---

### 2.5 Dependency Inversion Principle (DIP) - ❌ 明顯違反

**評分**: 2/10

**問題**：

**直接依賴 subprocess**
```python
# 所有 hook 直接依賴低層細節
subprocess.run(["git", "status", ...])
subprocess.run(["git", "add", ...])
subprocess.run(["git", "commit", ...])
```

**直接依賴檔案系統結構**
```python
# 硬編碼路徑結構
workflow_dir = Path(project_dir) / ".claude" / "workflow"
memory_dir = Path(project_dir) / ".claude" / "memory"
```

**應有設計**：
```python
# 依賴抽象
class GitRepository(Protocol):
    def has_changes(self, paths: list[str]) -> bool: ...
    def stage(self, paths: list[str]) -> None: ...
    def commit(self, message: str) -> CommitResult: ...

class WorkflowStateRepository(Protocol):
    def get_current_workflow_id(self) -> str: ...
    def update_state(self, **kwargs) -> None: ...

# Hook 依賴抽象，不依賴實作
def post_task_hook(git: GitRepository, state: WorkflowStateRepository):
    ...
```

---

## 3. 抽象層級建議

### 3.1 當前抽象層級（混亂）

```
┌─────────────────────────────────────┐
│ Hooks (post_task, subagent_stop...) │  ← 高層
├─────────────────────────────────────┤
│ update_state, log_action            │  ← 中層
├─────────────────────────────────────┤
│ subprocess.run(["git", ...])        │  ← 低層（直接依賴）
│ Path(...) / "current.json"          │  ← 低層（硬編碼）
└─────────────────────────────────────┘
```

**問題**：
- Hooks 同時處理高層業務邏輯和低層 Git 操作
- 缺乏中間抽象層
- 橫向重複（每個 hook 都重新實作相同邏輯）

---

### 3.2 建議抽象層級（分層清晰）

```
┌─────────────────────────────────────┐
│ Hooks (post_task, subagent_stop...) │  ← 高層：編排邏輯
├─────────────────────────────────────┤
│ GitCommitService                    │  ← 中層：業務抽象
│  - commit_task_changes()            │
│  - commit_memory_changes()          │
│  - generate_commit_message()        │
├─────────────────────────────────────┤
│ GitRepository                       │  ← 中層：Git 抽象
│  - has_changes(paths)               │
│  - stage(paths)                     │
│  - commit(message)                  │
├─────────────────────────────────────┤
│ WorkflowContext                     │  ← 中層：狀態抽象
│  - get_current_workflow_id()        │
│  - get_memory_type_mapping()        │
├─────────────────────────────────────┤
│ subprocess, Path, json              │  ← 低層：基礎設施
└─────────────────────────────────────┘
```

**優點**：
- 每層職責單一
- 橫向複用（`GitRepository` 可被所有 hook 使用）
- 易於測試（可 mock 中層抽象）
- 易於擴展（新增 hook 只需呼叫 `GitCommitService`）

---

### 3.3 什麼應該抽象？

#### 應該抽象（共用、變化、複雜）

| 邏輯 | 原因 | 優先級 |
|------|------|--------|
| `_get_current_workflow_id()` | 重複 5 次，完全相同 | 🔴 高 |
| Git status/add/commit 流程 | 模式重複 3+ 次 | 🔴 高 |
| Commit message 生成 | 散落各處，格式不一致 | 🟡 中 |
| Commit type 映射 | 資料重複，需要 SSOT | 🟡 中 |
| Co-Author 字串 | Magic string 重複 16+ 次 | 🟢 低 |
| Pathspec 構建 | 邏輯重複，易錯 | 🟢 低 |

#### 不該過度抽象（簡單、穩定、單次使用）

| 邏輯 | 原因 |
|------|------|
| `generate_id()` in `log_action.py` | 簡單、穩定、單一職責 |
| `Path.mkdir(parents=True, exist_ok=True)` | stdlib 已夠簡潔 |
| JSON 讀寫 | 簡單邏輯，抽象反而增加複雜度 |

---

### 3.4 建議的抽象層次

#### Level 1: 基礎抽象（立即實施）

```python
# shared/git/context.py
class WorkflowContext:
    """統一管理 workflow 狀態存取"""
    
    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir)
        self.workflow_dir = self.project_dir / ".claude" / "workflow"
    
    def get_current_workflow_id(self) -> str:
        """取得當前 workflow ID（取代重複的 _get_current_workflow_id）"""
        if self.workflow_dir.exists():
            for d in sorted(self.workflow_dir.iterdir(), reverse=True):
                if d.is_dir() and (d / "current.json").exists():
                    try:
                        with open(d / "current.json") as f:
                            state = json.load(f)
                            return state.get("workflow_id", d.name)
                    except Exception:
                        pass
        return ""
    
    def get_commit_type_for_memory(self, memory_type: str) -> str:
        """取得 memory type 對應的 commit type"""
        mapping = {
            "research": "docs",
            "plans": "feat",
            "tasks": "feat",
            "implement": "feat",
            "review": "docs",
            "verify": "test",
        }
        return mapping.get(memory_type, "chore")
```

**好處**：
- 消除 65 行重複代碼
- Single Source of Truth
- 易於測試（mock WorkflowContext 而非檔案系統）

---

#### Level 2: Git 操作抽象（中期實施）

```python
# shared/git/repository.py
@dataclass
class CommitResult:
    success: bool
    commit_hash: Optional[str] = None
    error: Optional[str] = None

class GitRepository:
    """封裝 Git 操作（取代直接使用 subprocess）"""
    
    CO_AUTHOR = "Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
    
    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir)
    
    def has_changes(self, paths: list[str] = None) -> bool:
        """檢查是否有變更"""
        cmd = ["git", "status", "--porcelain"]
        if paths:
            cmd.extend(["--"] + paths)
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            cwd=self.project_dir
        )
        return bool(result.stdout.strip())
    
    def stage(self, paths: list[str]) -> None:
        """Stage 檔案"""
        cmd = ["git", "add", "--"] + paths
        subprocess.run(cmd, cwd=self.project_dir, check=True)
    
    def commit(self, message: str, add_co_author: bool = True) -> CommitResult:
        """執行 commit"""
        if add_co_author and self.CO_AUTHOR not in message:
            message = f"{message}\n\n{self.CO_AUTHOR}"
        
        result = subprocess.run(
            ["git", "commit", "-m", message],
            capture_output=True,
            text=True,
            cwd=self.project_dir,
        )
        
        if result.returncode == 0:
            # 取得 commit hash
            hash_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.project_dir,
            )
            return CommitResult(
                success=True, 
                commit_hash=hash_result.stdout.strip()
            )
        else:
            return CommitResult(
                success=False, 
                error=result.stderr
            )
```

**好處**：
- 統一錯誤處理
- Co-Author 字串統一管理
- 返回結構化結果（而非裸 subprocess）
- 易於切換實作（如改用 GitPython）

---

#### Level 3: 業務邏輯抽象（長期實施）

```python
# shared/git/commit_service.py
class GitCommitService:
    """統一的 Git Commit 服務（業務邏輯層）"""
    
    def __init__(self, git: GitRepository, context: WorkflowContext):
        self.git = git
        self.context = context
    
    def commit_task_changes(
        self, 
        description: str,
        include_memory: bool = False,
        include_logs: bool = False,
        exclude_patterns: list[str] = None
    ) -> Optional[CommitResult]:
        """Task 完成後 commit 程式碼變更"""
        
        # 建立 pathspecs
        pathspecs = self._build_pathspecs(
            include_memory, 
            include_logs, 
            exclude_patterns or []
        )
        
        # 檢查變更
        if not self.git.has_changes(pathspecs):
            return None
        
        # Stage
        self.git.stage(pathspecs)
        
        # 生成 commit message
        task_summary = description[:50] if description else "task completed"
        message = f"chore(task): {task_summary}"
        
        # Commit
        return self.git.commit(message)
    
    def commit_memory_changes(
        self, 
        memory_type: str, 
        memory_id: str
    ) -> Optional[CommitResult]:
        """Commit 特定 memory 目錄"""
        
        memory_dir = f".claude/memory/{memory_type}/{memory_id}"
        
        # 檢查變更
        if not self.git.has_changes([memory_dir]):
            return None
        
        # Stage
        self.git.stage([memory_dir])
        
        # 生成 commit message
        commit_type = self.context.get_commit_type_for_memory(memory_type)
        topic = memory_id.replace("-", " ").replace("_", " ")
        
        # 取得變更檔案摘要
        summary = self._get_change_summary(memory_dir)
        
        message = f"""{commit_type}({memory_type}): complete {topic}

{summary}

Memory: {memory_dir}/"""
        
        # Commit
        return self.git.commit(message)
    
    def _build_pathspecs(
        self, 
        include_memory: bool,
        include_logs: bool,
        exclude_patterns: list[str]
    ) -> list[str]:
        """建立 pathspec 列表"""
        pathspecs = ["."]
        
        if not include_memory:
            pathspecs.append(":!.claude/memory/")
        
        if not include_logs:
            pathspecs.append(":!.claude/workflow/")
            pathspecs.append(":!.claude/logs/")
        
        for pattern in exclude_patterns:
            pathspecs.append(f":!{pattern}")
        
        return pathspecs
    
    def _get_change_summary(self, path: str, max_files: int = 3) -> str:
        """取得變更檔案摘要"""
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", path],
            capture_output=True,
            text=True,
            cwd=self.git.project_dir,
        )
        
        files = [f for f in result.stdout.strip().split("\n") if f]
        summary_lines = [f"- Update {Path(f).name}" for f in files[:max_files]]
        
        if len(files) > max_files:
            summary_lines.append(f"- ... and {len(files) - max_files} more files")
        
        return "\n".join(summary_lines)
```

**使用範例（重構後的 post_task.py）**：

```python
#!/usr/bin/env python3
"""Post-Task Hook - 在 Agent 完成後更新狀態並自動 commit"""

import json
import sys
from pathlib import Path

# 匯入共用模組
from shared.git.repository import GitRepository
from shared.git.context import WorkflowContext
from shared.git.commit_service import GitCommitService
from update_state import update_state
from log_action import log_action

def main():
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return
    
    project_dir = input_data.get("cwd", os.getcwd())
    tool_input = input_data.get("tool_input", {})
    description = tool_input.get("description", "")
    
    # 判斷成功或失敗
    tool_output = str(input_data.get("tool_response", ""))
    success = "error" not in tool_output.lower() and "failed" not in tool_output.lower()
    
    # 初始化服務層
    git = GitRepository(project_dir)
    context = WorkflowContext(project_dir)
    commit_service = GitCommitService(git, context)
    
    # 取得 workflow_id
    workflow_id = context.get_current_workflow_id()
    if not workflow_id:
        return
    
    agent_id = description.lower().replace(" ", "-")[:30]
    
    # 更新狀態
    update_state(
        project_dir=project_dir,
        workflow_id=workflow_id,
        agent_id=agent_id,
        agent_status="completed" if success else "failed",
    )
    
    # 記錄 action
    log_action(
        tool="Task",
        status="success" if success else "failed",
        input_data={"description": description},
        output_preview=tool_output[:200],
        project_dir=project_dir,
        workflow_id=workflow_id,
        agent_id=agent_id,
    )
    
    # 自動 commit（使用統一服務）
    if success:
        settings = _load_commit_settings(project_dir)
        if settings.get("enabled", True):
            commit_service.commit_task_changes(
                description=description,
                include_memory=settings.get("include_memory", False),
                include_logs=settings.get("include_logs", False),
                exclude_patterns=settings.get("exclude_patterns", []),
            )

if __name__ == "__main__":
    main()
```

**對比**：
- 原本 166 行 → 重構後約 60 行（減少 64%）
- 消除 `_get_current_workflow_id()` 重複
- 消除 Git 操作細節
- 更易理解、測試、維護

---

## 4. 簡化方向（降低認知負擔）

### 4.1 認知負擔分析

#### 當前認知地圖（新開發者視角）

```
要理解 Git Commit 流程需要：

1. 閱讀 5 個 hook 檔案 (共約 800 行)
   ├─ post_task.py (166 行)
   ├─ subagent_stop.py (196 行)
   ├─ pre_task.py (80 行)
   ├─ post_write.py (61 行)
   └─ subagent_start.py (81 行)

2. 理解 3 個共用模組
   ├─ update_state.py (145 行)
   ├─ log_action.py (152 行)
   └─ templates/workflow_hooks.py (183 行)

3. 閱讀 2 份文檔
   ├─ shared/git/commit-protocol.md
   └─ skills/memory-commit/SKILL.md

4. 對比差異
   └─ 為什麼同樣的邏輯有 3 種寫法？
   └─ commit_types 為什麼不統一？
   └─ 哪個是最新的實作？

總計需要理解 ~1500 行代碼 + 文檔
```

**認知負擔來源**：
- **分散性**：邏輯散落 8 個檔案
- **重複性**：需要對比 5 個版本的 `_get_current_workflow_id()`
- **不一致性**：3 種 commit message 生成方式
- **隱式契約**：為什麼 `post_task` 不 commit memory，但 `subagent_stop` 要？

#### 重構後認知地圖

```
要理解 Git Commit 流程需要：

1. 閱讀 1 個核心服務
   └─ shared/git/commit_service.py (~150 行)
      ├─ commit_task_changes()
      ├─ commit_memory_changes()
      └─ 清晰的文檔註解

2. 快速瀏覽 hooks（只看編排邏輯）
   └─ post_task.py (60 行，大部分是 boilerplate)

3. 理解配置
   └─ shared/config/commit-settings.yaml

總計需要理解 ~200 行代碼
```

**認知負擔降低**：
- 減少 87% 需要閱讀的代碼量
- 消除重複邏輯的對比成本
- 單一真相來源（SSOT）

---

### 4.2 簡化策略

#### 策略 1: 統一入口（Facade 模式）

**問題**：目前需要理解 Git + 狀態 + 日誌的組合

**解決**：提供統一的 Facade

```python
# shared/git/facade.py
class WorkflowCommitFacade:
    """統一的 Workflow Commit 入口（Facade）"""
    
    def __init__(self, project_dir: str):
        self.git = GitRepository(project_dir)
        self.context = WorkflowContext(project_dir)
        self.commit_service = GitCommitService(self.git, self.context)
        self.settings = self._load_settings(project_dir)
    
    def auto_commit_after_task(self, description: str, success: bool):
        """Task 完成後自動 commit（一行搞定）"""
        if not success or not self.settings.get("enabled", True):
            return
        
        return self.commit_service.commit_task_changes(
            description=description,
            **self.settings  # 自動展開配置
        )
    
    def auto_commit_memory(self, memory_type: str, memory_id: str):
        """Memory 變更自動 commit（一行搞定）"""
        return self.commit_service.commit_memory_changes(
            memory_type, memory_id
        )
```

**使用**：
```python
# post_task.py 簡化到極致
from shared.git.facade import WorkflowCommitFacade

def main():
    ...
    facade = WorkflowCommitFacade(project_dir)
    facade.auto_commit_after_task(description, success)
```

**認知負擔**：
- ❌ 前：需要理解 GitRepository + WorkflowContext + GitCommitService 三層
- ✅ 後：只需要知道 `facade.auto_commit_after_task()`

---

#### 策略 2: 配置驅動（減少硬編碼）

**問題**：commit type 映射、Co-Author 字串等散落代碼中

**解決**：集中到配置檔

```yaml
# shared/config/git-commit.yaml
commit:
  co_author: "Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
  
  memory_type_mapping:
    research: docs
    plans: feat
    tasks: feat
    implement: feat
    review: docs
    verify: test
  
  message_templates:
    task: "chore(task): {summary}"
    memory: "{type}({scope}): complete {topic}\n\n{changes}\n\nMemory: {path}/"
```

**好處**：
- 修改配置不需要改代碼
- 新增 memory type 只需編輯 YAML
- 文檔與實作統一（讀配置檔即文檔）

---

#### 策略 3: 慣例優於配置（Convention over Configuration）

**問題**：太多配置選項增加認知負擔

**解決**：建立合理預設

```python
# 預設慣例
DEFAULT_CONVENTIONS = {
    # Task commit 預設不包含 memory/logs（由專門的 hook 處理）
    "task_commit_includes_memory": False,
    "task_commit_includes_logs": False,
    
    # Memory commit 預設按目錄自動推斷 type
    "memory_commit_auto_detect_type": True,
    
    # Co-Author 預設自動添加
    "auto_add_co_author": True,
}
```

**使用者只在需要偏離慣例時才配置**：
```yaml
# 大部分專案不需要配置檔，使用預設即可
# 只有特殊需求才覆寫
task_commit:
  include_memory: true  # 非預設，需要明確配置
```

---

#### 策略 4: 自解釋代碼（Self-Documenting Code）

**問題**：需要對照代碼 + 文檔才能理解

**解決**：代碼即文檔

**反例（當前）**：
```python
pathspecs.append(":!.claude/memory/")  # 什麼是 :!？為什麼排除 memory？
```

**正例（重構後）**：
```python
class PathspecBuilder:
    """Git pathspec 建構器
    
    Pathspec 語法：
    - `.` = 所有檔案
    - `:!path/` = 排除 path/
    """
    
    def exclude(self, path: str) -> 'PathspecBuilder':
        """排除指定路徑（使用 git pathspec 的 :! 語法）"""
        self.specs.append(f":!{path}")
        return self
    
    def build(self) -> list[str]:
        return self.specs

# 使用
pathspecs = (
    PathspecBuilder()
    .include_all()
    .exclude(".claude/memory/")  # Memory 由 subagent_stop hook 處理
    .exclude(".claude/logs/")     # Logs 通常不需要 commit
    .build()
)
```

**好處**：
- 不需要查文檔就知道用途
- 型別提示 + 註解 = 內建文檔
- 鏈式呼叫增加可讀性

---

### 4.3 學習曲線優化

#### 當前學習路徑（陡峭）

```
Day 1: 讀完 5 個 hook，困惑為什麼重複
Day 2: 讀 commit-protocol.md，發現與代碼不一致
Day 3: 對比不同實作，找出差異
Day 4: 嘗試修改，發現要改 5 個地方
Day 5: 放棄，直接複製貼上
```

#### 重構後學習路徑（平緩）

```
Day 1: 讀 GitCommitService 文檔，理解核心概念
       └─ 2 個方法：commit_task_changes, commit_memory_changes
Day 2: 看一個 hook 範例（post_task.py），學會使用 Facade
Day 3: 開始寫新 hook，直接複用服務層
Day 4: 需要自訂？修改配置檔或擴展 Formatter
```

---

## 5. 設計模式建議

### 5.1 Facade（外觀模式）- 🔴 高優先級

**目的**：簡化複雜子系統的使用

**應用**：`WorkflowCommitFacade`（見 4.2 策略 1）

**效益**：
- 降低 Hook 開發者的認知負擔
- 隱藏 Git + 狀態 + 配置的複雜性
- 提供簡潔的 API

---

### 5.2 Strategy（策略模式）- 🟡 中優先級

**目的**：封裝可替換的演算法

**應用場景 1 - Commit Message 格式化**

```python
class CommitMessageFormatter(ABC):
    @abstractmethod
    def format(self, commit_type: str, scope: str, description: str, **kwargs) -> str:
        pass

class ConventionalCommitsFormatter(CommitMessageFormatter):
    """Conventional Commits 格式"""
    def format(self, commit_type, scope, description, **kwargs):
        message = f"{commit_type}({scope}): {description}"
        
        if details := kwargs.get("details"):
            message += f"\n\n{details}"
        
        if memory_path := kwargs.get("memory_path"):
            message += f"\n\nMemory: {memory_path}/"
        
        return message

class SimpleFormatter(CommitMessageFormatter):
    """簡單格式（不使用 Conventional Commits）"""
    def format(self, commit_type, scope, description, **kwargs):
        return f"[{scope}] {description}"

# 使用
formatter = ConventionalCommitsFormatter()  # 可替換
message = formatter.format("feat", "plan", "user auth design", details="...")
```

**應用場景 2 - Pathspec 建構策略**

```python
class PathspecStrategy(ABC):
    @abstractmethod
    def build(self, settings: dict) -> list[str]:
        pass

class TaskPathspecStrategy(PathspecStrategy):
    """Task commit 的 pathspec（排除 memory/logs）"""
    def build(self, settings):
        specs = ["."]
        if not settings.get("include_memory"):
            specs.append(":!.claude/memory/")
        if not settings.get("include_logs"):
            specs.append(":!.claude/workflow/")
            specs.append(":!.claude/logs/")
        return specs

class MemoryPathspecStrategy(PathspecStrategy):
    """Memory commit 的 pathspec（只包含特定目錄）"""
    def build(self, settings):
        memory_dir = settings.get("memory_dir")
        return [memory_dir]
```

**效益**：
- 易於擴展新格式（不修改現有代碼）
- 可通過配置切換策略
- 符合 Open/Closed 原則

---

### 5.3 Template Method（模板方法）- 🟡 中優先級

**目的**：定義演算法骨架，細節由子類實作

**應用**：統一 Commit 流程

```python
class BaseCommitHandler(ABC):
    """Commit 流程模板"""
    
    def execute(self) -> Optional[CommitResult]:
        """模板方法：定義 commit 流程骨架"""
        
        # Step 1: 檢查變更
        if not self.has_changes():
            return None
        
        # Step 2: Stage 檔案
        paths = self.get_paths_to_stage()
        self.git.stage(paths)
        
        # Step 3: 生成 commit message（子類實作）
        message = self.generate_commit_message()
        
        # Step 4: Commit
        result = self.git.commit(message)
        
        # Step 5: 後處理（子類可覆寫）
        self.post_commit(result)
        
        return result
    
    @abstractmethod
    def get_paths_to_stage(self) -> list[str]:
        """子類決定要 stage 哪些檔案"""
        pass
    
    @abstractmethod
    def generate_commit_message(self) -> str:
        """子類決定 commit message 格式"""
        pass
    
    def has_changes(self) -> bool:
        """預設實作（子類可覆寫）"""
        return self.git.has_changes(self.get_paths_to_stage())
    
    def post_commit(self, result: CommitResult):
        """後處理鉤子（子類可覆寫）"""
        pass

class TaskCommitHandler(BaseCommitHandler):
    """Task commit 的具體實作"""
    
    def __init__(self, git, description, settings):
        self.git = git
        self.description = description
        self.settings = settings
    
    def get_paths_to_stage(self):
        # 複用 PathspecBuilder
        return PathspecBuilder().exclude_memory_and_logs().build()
    
    def generate_commit_message(self):
        summary = self.description[:50]
        return f"chore(task): {summary}"

class MemoryCommitHandler(BaseCommitHandler):
    """Memory commit 的具體實作"""
    
    def get_paths_to_stage(self):
        return [f".claude/memory/{self.memory_type}/{self.memory_id}"]
    
    def generate_commit_message(self):
        commit_type = self.context.get_commit_type_for_memory(self.memory_type)
        topic = self.memory_id.replace("-", " ")
        return f"{commit_type}({self.memory_type}): complete {topic}"
```

**效益**：
- 避免重複 commit 流程代碼
- 新增 commit 類型只需實作 2 個方法
- 流程一致性保證

---

### 5.4 Repository（倉儲模式）- 🔴 高優先級

**目的**：封裝資料存取邏輯

**已建議**：見 3.4 的 `GitRepository` 和 `WorkflowContext`

**效益**：
- 隱藏底層 subprocess 和檔案系統細節
- 易於測試（mock Repository）
- 易於切換實作（如改用 GitPython）

---

### 5.5 Builder（建造者模式）- 🟢 低優先級

**目的**：分步驟建構複雜物件

**應用**：Commit Message 建構

```python
class CommitMessageBuilder:
    """Commit message 建構器"""
    
    def __init__(self):
        self._type = None
        self._scope = None
        self._subject = None
        self._body_lines = []
        self._footers = {}
    
    def type(self, type_: str) -> 'CommitMessageBuilder':
        self._type = type_
        return self
    
    def scope(self, scope: str) -> 'CommitMessageBuilder':
        self._scope = scope
        return self
    
    def subject(self, subject: str) -> 'CommitMessageBuilder':
        self._subject = subject
        return self
    
    def add_detail(self, detail: str) -> 'CommitMessageBuilder':
        self._body_lines.append(detail)
        return self
    
    def add_footer(self, key: str, value: str) -> 'CommitMessageBuilder':
        self._footers[key] = value
        return self
    
    def memory_path(self, path: str) -> 'CommitMessageBuilder':
        self._footers["Memory"] = f"{path}/"
        return self
    
    def build(self) -> str:
        """建構最終 commit message"""
        parts = []
        
        # Header
        header = f"{self._type}({self._scope}): {self._subject}"
        parts.append(header)
        
        # Body
        if self._body_lines:
            parts.append("")
            parts.extend(self._body_lines)
        
        # Footers
        if self._footers:
            parts.append("")
            for key, value in self._footers.items():
                parts.append(f"{key}: {value}")
        
        # Co-Author（自動添加）
        parts.append("")
        parts.append("Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>")
        
        return "\n".join(parts)

# 使用
message = (
    CommitMessageBuilder()
    .type("feat")
    .scope("plan")
    .subject("user authentication design")
    .add_detail("- 3 perspectives analyzed")
    .add_detail("- Security reviewed")
    .memory_path(".claude/memory/plans/user-auth")
    .build()
)
```

**效益**：
- 鏈式呼叫增加可讀性
- 保證 message 格式一致
- 易於擴展新欄位

---

### 5.6 Observer（觀察者模式）- 🟢 低優先級

**目的**：解耦事件發送者和接收者

**應用**：Commit 事件通知

```python
class CommitObserver(ABC):
    @abstractmethod
    def on_commit_success(self, result: CommitResult):
        pass
    
    @abstractmethod
    def on_commit_failed(self, error: str):
        pass

class LoggingCommitObserver(CommitObserver):
    """記錄 commit 到 actions.jsonl"""
    def on_commit_success(self, result):
        log_action(tool="Git", status="success", ...)
    
    def on_commit_failed(self, error):
        log_action(tool="Git", status="failed", error=error)

class NotificationCommitObserver(CommitObserver):
    """發送通知（未來擴展）"""
    def on_commit_success(self, result):
        notify_user(f"Committed: {result.commit_hash}")

# GitRepository 支援 Observer
class GitRepository:
    def __init__(self):
        self.observers: list[CommitObserver] = []
    
    def add_observer(self, observer: CommitObserver):
        self.observers.append(observer)
    
    def commit(self, message: str) -> CommitResult:
        result = self._do_commit(message)
        
        # 通知所有觀察者
        if result.success:
            for obs in self.observers:
                obs.on_commit_success(result)
        else:
            for obs in self.observers:
                obs.on_commit_failed(result.error)
        
        return result
```

**效益**：
- 解耦 Git 操作和日誌記錄
- 易於添加新的 commit 後處理（如通知、統計）

---

## 6. 重構優先級與影響評估

### 6.1 立即實施（Quick Wins）

| 重構項目 | 工作量 | 影響 | ROI |
|---------|-------|------|-----|
| 抽取 `WorkflowContext.get_current_workflow_id()` | 2h | -65 行重複代碼 | 🔥🔥🔥 |
| 統一 Co-Author 字串為常數 | 1h | -16 處重複 | 🔥🔥 |
| 建立 `commit-types.yaml` 配置 | 1h | SSOT | 🔥🔥 |

**總計**：約 4 小時，消除 ~100 行重複代碼

---

### 6.2 中期實施（High Impact）

| 重構項目 | 工作量 | 影響 | ROI |
|---------|-------|------|-----|
| 實作 `GitRepository` 抽象層 | 1d | 統一 Git 操作 + 錯誤處理 | 🔥🔥🔥 |
| 實作 `GitCommitService` 業務層 | 1d | 消除 commit 邏輯重複 | 🔥🔥🔥 |
| 重構所有 hooks 使用新服務 | 0.5d | -400 行代碼 | 🔥🔥 |
| 添加單元測試 | 1d | 提升信心 | 🔥 |

**總計**：約 3.5 天，消除 ~60% 重複代碼

---

### 6.3 長期實施（Nice to Have）

| 重構項目 | 工作量 | 影響 | ROI |
|---------|-------|------|-----|
| Strategy 模式（Formatter） | 0.5d | 擴展性 | 🔥 |
| Template Method（CommitHandler） | 0.5d | 流程一致性 | 🔥 |
| Builder（CommitMessageBuilder） | 0.5d | 可讀性 | 🔥 |
| Observer（Commit 事件） | 0.5d | 解耦 | 🔥 |

**總計**：約 2 天，提升擴展性和可維護性

---

### 6.4 風險評估

| 風險 | 機率 | 影響 | 緩解措施 |
|------|-----|------|---------|
| 破壞現有 hook 行為 | 中 | 高 | 完整單元測試 + 整合測試 |
| 引入新 bug | 中 | 中 | 分階段重構 + code review |
| 學習曲線 | 低 | 低 | 提供文檔 + 範例 |
| 效能下降 | 極低 | 低 | 抽象層很薄，影響可忽略 |

---

## 7. 結論與建議

### 7.1 核心問題總結

1. **DRY 違反嚴重**：`_get_current_workflow_id()` 重複 5 次，Git 操作模式重複 3+ 次
2. **SOLID 違反**：
   - OCP：新增 commit type 需修改代碼
   - DIP：直接依賴 subprocess 和檔案系統
3. **認知負擔高**：需理解 ~1500 行分散代碼
4. **缺乏抽象**：無統一的 Git 操作層和業務邏輯層

---

### 7.2 重構路線圖

#### Phase 1: 基礎重構（Week 1）
- [ ] 抽取 `WorkflowContext` 類別
- [ ] 統一 Co-Author 常數
- [ ] 建立 `commit-types.yaml` 配置
- [ ] 編寫單元測試

**目標**：消除 65 行重複代碼，建立 SSOT

---

#### Phase 2: 抽象層（Week 2-3）
- [ ] 實作 `GitRepository` 抽象
- [ ] 實作 `GitCommitService` 業務層
- [ ] 建立 `WorkflowCommitFacade`
- [ ] 重構 `post_task.py` 使用新架構
- [ ] 編寫整合測試

**目標**：建立清晰的抽象層次

---

#### Phase 3: 全面重構（Week 4）
- [ ] 重構所有 hooks 使用新服務
- [ ] 實作 Strategy 模式（Formatter）
- [ ] 實作 Template Method（CommitHandler）
- [ ] 更新文檔

**目標**：消除所有重複，達成 SOLID

---

#### Phase 4: 優化擴展（Week 5）
- [ ] 實作 Builder（CommitMessageBuilder）
- [ ] 實作 Observer（Commit 事件）
- [ ] 效能優化
- [ ] 完整測試覆蓋

**目標**：提升擴展性和可維護性

---

### 7.3 預期效益

| 指標 | 改善 |
|------|------|
| 代碼行數 | -60% (~500 行) |
| 重複代碼 | -95% |
| 新 hook 開發時間 | -70% |
| 測試覆蓋率 | +40% |
| 新人理解時間 | -80% (5天 → 1天) |
| Bug 修復速度 | +50% |

---

### 7.4 最終建議

**立即行動**：
1. 實作 `WorkflowContext` 類別（2h，高 ROI）
2. 統一 Co-Author 常數（1h，低風險）

**中期規劃**：
3. 建立 `GitRepository` + `GitCommitService` 抽象層（3.5 天）
4. 漸進式重構 hooks（每個 0.5 天）

**長期願景**：
5. 完整的設計模式應用（2 天）
6. 100% 測試覆蓋（持續）

**關鍵原則**：
- 分階段重構，每階段可獨立運行
- 測試先行（TDD）
- 保持向後相容（至少在重構期間）
- 文檔同步更新

---

## 附錄：重構範例對比

### A. 重構前（post_task.py）

```python
# 166 行，混雜多個職責
def _get_current_workflow_id(project_dir: str) -> str:
    # ... 13 行重複代碼

def _commit_task_changes(project_dir: str, description: str, success: bool):
    # ... 49 行 Git 操作細節
    cmd = ["git", "status", "--porcelain", "--"] + pathspecs
    result = subprocess.run(...)
    # ...

def main():
    # ... 混雜狀態更新、日誌記錄、Git commit
```

---

### B. 重構後（post_task.py）

```python
# 60 行，職責清晰
from shared.git.facade import WorkflowCommitFacade
from update_state import update_state
from log_action import log_action

def main():
    # 業務邏輯清晰
    facade = WorkflowCommitFacade(project_dir)
    workflow_id = facade.context.get_current_workflow_id()
    
    update_state(...)
    log_action(...)
    
    # Git commit 一行搞定
    if success:
        facade.auto_commit_after_task(description, success)
```

**差異**：
- 代碼量：166 → 60 行（-64%）
- 重複消除：100%
- 可讀性：大幅提升
- 可測試性：容易 mock `WorkflowCommitFacade`

---

## 參考資料

- [DRY Principle](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [Design Patterns: Elements of Reusable Object-Oriented Software](https://en.wikipedia.org/wiki/Design_Patterns)
- [Clean Code by Robert C. Martin](https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882)
- [Refactoring: Improving the Design of Existing Code](https://martinfowler.com/books/refactoring.html)
