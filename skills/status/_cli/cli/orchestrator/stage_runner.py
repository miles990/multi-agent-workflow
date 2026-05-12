"""
階段執行器 - 執行單一階段的完整流程

流程：
1. 初始化階段目錄
2. 並行調用視角 Agent
3. 收集並驗證結果
4. 生成綜合報告
5. 品質閘門檢查
"""

import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config.models import (
    AgentResponse,
    AgentStatus,
    PerspectiveConfig,
    StageConfig,
    StageID,
    StageResult,
)
from ..config.artifacts import get_stage_artifact_manifest
from ..config.perspectives import get_stage_perspectives
from ..config.stages import get_stage
from ..io.logging import ActionLogger
from ..io.memory import MemoryManager
from ..io.state import StateTracker
from .agent_caller import AgentCaller, ParallelAgentCaller
from .errors import StageError, ValidationError


class StageRunner:
    """階段執行器"""

    def __init__(
        self,
        workflow_id: str,
        memory: MemoryManager,
        logger: ActionLogger,
        tracker: StateTracker,
        caller: Optional[AgentCaller] = None,
    ):
        """
        初始化階段執行器

        Args:
            workflow_id: 工作流 ID
            memory: Memory 管理器
            logger: Action Logger
            tracker: 狀態追蹤器
            caller: Agent 調用器
        """
        self.workflow_id = workflow_id
        self.memory = memory
        self.logger = logger
        self.tracker = tracker
        self.caller = caller or AgentCaller()
        self.parallel_caller = ParallelAgentCaller(self.caller)

    def run(
        self,
        stage_id: StageID,
        context: Dict[str, Any],
        quick_mode: bool = False,
    ) -> StageResult:
        """
        執行階段

        Args:
            stage_id: 階段 ID
            context: 執行上下文（包含前階段輸出等）
            quick_mode: 是否快速模式（減少視角數量）

        Returns:
            StageResult 物件
        """
        start_time = time.time()
        stage_config = get_stage(stage_id)
        errors: List[str] = []
        outputs: Dict[str, str] = {}

        # 1. 初始化階段
        self._init_stage(stage_id, stage_config)

        try:
            # 2. 取得視角列表
            perspectives = get_stage_perspectives(stage_id, quick_mode)
            self.logger.stage_start(
                stage_id=stage_id.value,
                stage_name=stage_config.name,
                perspectives=[p.id for p in perspectives],
            )

            # 3. 設定 Agent 狀態
            self._setup_agents(perspectives)

            # 4. 並行執行視角 Agent
            perspective_results = self._run_perspectives(
                stage_id,
                perspectives,
                context,
            )

            # 5. 驗證並保存結果
            outputs = self._save_perspective_reports(
                stage_id,
                perspective_results,
            )

            # 6. 生成綜合報告
            synthesis_path = self._generate_synthesis(
                stage_id,
                perspective_results,
                context,
            )
            if synthesis_path:
                manifest = get_stage_artifact_manifest(stage_id)
                if synthesis_path == manifest.primary_output_path(synthesis_path.parent):
                    outputs[manifest.primary_output_key] = str(synthesis_path)
                outputs.setdefault("synthesis", str(synthesis_path))

            # 7. 計算品質分數
            quality_score = self._calculate_quality_score(
                stage_id,
                perspective_results,
            )

            duration = time.time() - start_time
            self.logger.stage_complete(
                stage_id=stage_id.value,
                success=True,
                duration_seconds=duration,
            )

            return StageResult(
                stage_id=stage_id,
                success=True,
                outputs=outputs,
                quality_score=quality_score,
                errors=errors,
                duration_seconds=duration,
            )

        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            errors.append(error_msg)

            self.logger.stage_complete(
                stage_id=stage_id.value,
                success=False,
                duration_seconds=duration,
            )

            return StageResult(
                stage_id=stage_id,
                success=False,
                outputs=outputs,
                errors=errors,
                duration_seconds=duration,
            )

    def _init_stage(self, stage_id: StageID, config: StageConfig) -> Path:
        """初始化階段目錄"""
        from ..config.stages import get_stage_index, STAGE_ORDER

        stage_dir = self.memory.create_stage_dir(self.workflow_id, stage_id.value)
        get_stage_artifact_manifest(stage_id).ensure_directories(stage_dir)

        # 更新狀態
        self.tracker.set_stage(
            stage_id=stage_id.value,
            stage_name=config.name,
            description=config.description,
            index=get_stage_index(stage_id),
            total=len(STAGE_ORDER),
        )

        # 更新工作流 meta
        self.memory.update_stage_status(
            self.workflow_id,
            stage_id.value,
            "running",
        )

        return stage_dir

    def _setup_agents(self, perspectives: List[PerspectiveConfig]) -> None:
        """設定 Agent 狀態追蹤"""
        for p in perspectives:
            self.tracker.add_agent(
                agent_id=p.id,
                agent_name=p.name,
                description=p.description,
                model=p.model,
            )

    def _run_perspectives(
        self,
        stage_id: StageID,
        perspectives: List[PerspectiveConfig],
        context: Dict,
    ) -> Dict[str, AgentResponse]:
        """
        並行執行視角 Agent

        Args:
            stage_id: 階段 ID
            perspectives: 視角配置列表
            context: 執行上下文

        Returns:
            以視角 ID 為 key 的結果字典
        """
        from ..prompts import get_perspective_prompt

        # 構建 Agent 任務
        agents = []
        for p in perspectives:
            # 更新狀態
            self.tracker.update_agent_status(p.id, "running")
            self.logger.agent_start(
                agent_id=p.id,
                agent_name=p.name,
                model=p.model,
                task=f"執行 {p.name} 視角分析",
            )

            prompt = get_perspective_prompt(stage_id, p, context)
            agents.append({
                "id": p.id,
                "prompt": prompt,
                "model": p.model,
            })

        # 並行執行
        results = self.parallel_caller.call_parallel(agents, context)

        # 更新狀態
        for p in perspectives:
            result = results.get(p.id)
            if result and result.success:
                self.tracker.update_agent_status(p.id, "completed")
                self.logger.agent_complete(
                    agent_id=p.id,
                    success=True,
                    duration_seconds=result.duration_seconds,
                )
            else:
                self.tracker.update_agent_status(p.id, "failed")
                self.logger.agent_call_error(
                    agent_id=p.id,
                    reason=result.error if result else "Unknown error",
                    attempt=1,
                    retryable=False,
                )

        return results

    def _save_perspective_reports(
        self,
        stage_id: StageID,
        results: Dict[str, AgentResponse],
    ) -> Dict[str, str]:
        """保存視角報告"""
        outputs = {}
        stage_dir = self.memory.get_stage_dir(self.workflow_id, stage_id.value)

        if not stage_dir:
            return outputs

        manifest = get_stage_artifact_manifest(stage_id)

        for perspective_id, response in results.items():
            if not response.success or not response.content:
                continue

            # 保存 JSON
            json_path = manifest.perspective_json_path(stage_dir, perspective_id)
            self.memory.write_json(json_path, response.content)
            outputs[f"perspective_{perspective_id}"] = str(json_path)

            # 記錄檔案寫入
            self.logger.file_write(
                str(json_path),
                json_path.stat().st_size if json_path.exists() else 0,
            )

            # 生成 Markdown 報告
            md_path = manifest.perspective_markdown_path(stage_dir, perspective_id)
            md_content = self._render_perspective_markdown(perspective_id, response.content)
            self.memory.write_text(md_path, md_content)

        return outputs

    def _render_perspective_markdown(
        self,
        perspective_id: str,
        content: Dict,
    ) -> str:
        """將視角報告渲染為 Markdown"""
        lines = []

        # 標題
        name = content.get("perspective_name", perspective_id)
        lines.append(f"# {name}")
        lines.append("")

        # 摘要
        if summary := content.get("summary"):
            lines.append(f"> {summary}")
            lines.append("")

        # 主要發現
        if findings := content.get("findings"):
            lines.append("## 主要發現")
            lines.append("")
            for f in findings:
                importance = f.get("importance", "medium")
                icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(importance, "")
                lines.append(f"### {icon} {f.get('title', 'Finding')}")
                lines.append(f.get("description", ""))
                lines.append("")

        # 建議
        if recommendations := content.get("recommendations"):
            lines.append("## 建議")
            lines.append("")
            for r in recommendations:
                priority = r.get("priority", "should")
                icon = {"must": "🔴", "should": "🟡", "could": "🟢"}.get(priority, "")
                lines.append(f"- {icon} **{r.get('title', '')}**: {r.get('description', '')}")
            lines.append("")

        # 擔憂
        if concerns := content.get("concerns"):
            lines.append("## 擔憂與風險")
            lines.append("")
            for c in concerns:
                severity = c.get("severity", "medium")
                icon = {"critical": "🚨", "high": "🔴", "medium": "🟡", "low": "🟢"}.get(severity, "")
                lines.append(f"- {icon} **{c.get('title', '')}**: {c.get('description', '')}")
            lines.append("")

        return "\n".join(lines)

    def _generate_synthesis(
        self,
        stage_id: StageID,
        results: Dict[str, AgentResponse],
        context: Dict,
    ) -> Optional[Path]:
        """生成綜合報告"""
        from ..prompts import get_synthesis_prompt

        # 收集所有視角內容
        perspective_contents = {}
        for pid, response in results.items():
            if response.success and response.content:
                perspective_contents[pid] = response.content

        if not perspective_contents:
            return None

        # 調用綜合 Agent
        prompt = get_synthesis_prompt(stage_id, perspective_contents, context)
        response = self.caller.call(prompt, model="sonnet")

        if not response.success or not response.content:
            return None

        # 保存綜合報告
        stage_dir = self.memory.get_stage_dir(self.workflow_id, stage_id.value)
        if not stage_dir:
            return None

        manifest = get_stage_artifact_manifest(stage_id)

        # JSON 格式
        json_path = manifest.synthesis_json_path(stage_dir)
        self.memory.write_json(json_path, response.content)

        # Markdown 格式
        md_path = manifest.synthesis_markdown_path(stage_dir)
        md_content = self._render_synthesis_markdown(stage_id, response.content)
        self.memory.write_text(md_path, md_content)

        self.logger.file_write(str(md_path), md_path.stat().st_size if md_path.exists() else 0)

        return md_path

    def _render_synthesis_markdown(
        self,
        stage_id: StageID,
        content: Dict,
    ) -> str:
        """將綜合報告渲染為 Markdown"""
        lines = []

        stage_config = get_stage(stage_id)
        lines.append(f"# {stage_config.name} - 綜合報告")
        lines.append("")

        # 共識
        if consensus := content.get("consensus"):
            score = consensus.get("score", 0)
            lines.append(f"## 共識度: {score * 100:.0f}%")
            lines.append("")
            if points := consensus.get("points"):
                for point in points:
                    lines.append(f"- {point}")
                lines.append("")

        # 關鍵洞察
        if insights := content.get("key_insights"):
            lines.append("## 關鍵洞察")
            lines.append("")
            for insight in insights:
                sources = ", ".join(insight.get("source_perspectives", []))
                confidence = insight.get("confidence", "medium")
                lines.append(f"- **{insight.get('insight', '')}**")
                lines.append(f"  - 來源: {sources}")
                lines.append(f"  - 信心度: {confidence}")
            lines.append("")

        # 衝突點
        if conflicts := content.get("conflicts"):
            lines.append("## 衝突點")
            lines.append("")
            for conflict in conflicts:
                lines.append(f"### {conflict.get('topic', '')}")
                for p in conflict.get("perspectives", []):
                    lines.append(f"- **{p.get('perspective_id', '')}**: {p.get('position', '')}")
                if resolution := conflict.get("resolution"):
                    lines.append(f"- **決議**: {resolution}")
                lines.append("")

        # 行動項目
        if actions := content.get("action_items"):
            lines.append("## 行動項目")
            lines.append("")
            for action in actions:
                priority = action.get("priority", "medium")
                icon = {"critical": "🚨", "high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "")
                lines.append(f"- {icon} {action.get('action', '')}")
            lines.append("")

        return "\n".join(lines)

    def _calculate_quality_score(
        self,
        stage_id: StageID,
        results: Dict[str, AgentResponse],
    ) -> float:
        """計算品質分數"""
        if not results:
            return 0.0

        # 基礎分數：成功率
        success_count = sum(1 for r in results.values() if r.success)
        success_rate = success_count / len(results)

        # 內容品質分數
        content_score = 0.0
        for response in results.values():
            if response.success and response.content:
                # 檢查必要欄位
                has_findings = bool(response.content.get("findings"))
                has_recommendations = bool(response.content.get("recommendations"))
                content_score += (0.5 if has_findings else 0) + (0.5 if has_recommendations else 0)

        if success_count > 0:
            content_score /= success_count

        # 綜合分數 (0-100)
        return (success_rate * 50 + content_score * 50)
