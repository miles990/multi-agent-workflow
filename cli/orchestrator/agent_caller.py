"""
Agent 調用模組 - 限制工具、強制 JSON 返回

核心原則：
- Agent 只負責思考和分析
- 限制工具：只允許 Read/Glob/Grep/Bash/WebFetch
- 禁止：Write/Task（確定性操作由 CLI 執行）
- 強制 JSON 輸出
"""

import json
import re
import subprocess
import time
from typing import Any, Dict, List, Optional

from ..config.models import AgentResponse
from .errors import AgentError


# 允許的工具列表
ALLOWED_TOOLS = [
    "Read",
    "Glob",
    "Grep",
    "Bash",
    "WebFetch",
    "WebSearch",
]

# 禁止的工具
FORBIDDEN_TOOLS = [
    "Write",
    "Edit",
    "Task",
    "NotebookEdit",
]


class AgentCaller:
    """Agent 調用器"""

    def __init__(
        self,
        default_model: str = "sonnet",
        timeout: int = 300,
        max_retries: int = 3,
    ):
        """
        初始化 Agent 調用器

        Args:
            default_model: 預設模型
            timeout: 超時時間（秒）
            max_retries: 最大重試次數
        """
        self.default_model = default_model
        self.timeout = timeout
        self.max_retries = max_retries

    def call(
        self,
        prompt: str,
        model: Optional[str] = None,
        output_format: str = "json",
        context: Optional[Dict] = None,
    ) -> AgentResponse:
        """
        調用 Agent 並獲取 JSON 回應

        Args:
            prompt: Prompt 內容
            model: 使用的模型（預設使用 default_model）
            output_format: 輸出格式（json/text）
            context: 額外上下文

        Returns:
            AgentResponse 物件
        """
        model = model or self.default_model
        start_time = time.time()

        # 構建完整 prompt
        full_prompt = self._build_prompt(prompt, output_format, context)

        # 重試邏輯
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                result = self._execute_claude(full_prompt, model)
                duration = time.time() - start_time

                # 解析回應
                if output_format == "json":
                    content = self._parse_json_response(result)
                    return AgentResponse(
                        success=True,
                        content=content,
                        raw_output=result,
                        duration_seconds=duration,
                    )
                else:
                    return AgentResponse(
                        success=True,
                        content={"text": result},
                        raw_output=result,
                        duration_seconds=duration,
                    )

            except AgentError as e:
                last_error = e
                if not e.retryable or attempt >= self.max_retries:
                    break
                time.sleep(2 ** attempt)  # 指數退避

            except Exception as e:
                last_error = AgentError(
                    f"Unexpected error: {str(e)}",
                    retryable=False,
                )
                break

        # 所有重試失敗
        duration = time.time() - start_time
        return AgentResponse(
            success=False,
            error=str(last_error) if last_error else "Unknown error",
            duration_seconds=duration,
        )

    def _build_prompt(
        self,
        prompt: str,
        output_format: str,
        context: Optional[Dict],
    ) -> str:
        """構建完整 prompt"""
        parts = []

        # 系統指令
        parts.append(self._get_system_instructions(output_format))

        # 上下文
        if context:
            parts.append(f"\n## Context\n```json\n{json.dumps(context, ensure_ascii=False, indent=2)}\n```")

        # 主要任務
        parts.append(f"\n## Task\n{prompt}")

        # 輸出格式要求
        if output_format == "json":
            parts.append(self._get_json_output_instructions())

        return "\n".join(parts)

    def _get_system_instructions(self, output_format: str) -> str:
        """取得系統指令"""
        return """# Agent Instructions

You are an analysis agent. Your role is to think, analyze, and provide insights.

## Important Rules
1. You are NOT allowed to write files or create tasks
2. You can only use Read, Glob, Grep, Bash, WebFetch, WebSearch tools
3. Focus on analysis and return structured results
4. Be thorough but concise"""

    def _get_json_output_instructions(self) -> str:
        """取得 JSON 輸出指令"""
        return """

## Output Format

You MUST return your response as valid JSON.
- Start your final answer with ```json
- End with ```
- Ensure the JSON is valid and parseable
- Do not include any text outside the JSON block in your final response"""

    def _execute_claude(self, prompt: str, model: str) -> str:
        """
        執行 Claude CLI

        Args:
            prompt: 完整 prompt
            model: 模型名稱

        Returns:
            CLI 輸出
        """
        # 構建命令
        cmd = [
            "claude",
            "--print",
            "--model", model,
            "--allowedTools", ",".join(ALLOWED_TOOLS),
        ]

        try:
            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            if result.returncode != 0:
                error_msg = result.stderr or "Unknown error"
                raise AgentError(
                    f"Claude CLI failed: {error_msg}",
                    retryable=True,
                )

            return result.stdout

        except subprocess.TimeoutExpired:
            raise AgentError(
                f"Agent timed out after {self.timeout}s",
                retryable=True,
            )
        except FileNotFoundError:
            raise AgentError(
                "Claude CLI not found. Please install claude-code.",
                retryable=False,
            )

    def _parse_json_response(self, output: str) -> Dict[str, Any]:
        """
        解析 JSON 回應

        Args:
            output: CLI 輸出

        Returns:
            解析後的 JSON 物件
        """
        # 嘗試找到 JSON 區塊
        json_patterns = [
            r"```json\s*([\s\S]*?)\s*```",  # ```json ... ```
            r"```\s*([\s\S]*?)\s*```",       # ``` ... ```
            r"\{[\s\S]*\}",                   # 直接 JSON
        ]

        for pattern in json_patterns:
            matches = re.findall(pattern, output, re.MULTILINE)
            if matches:
                # 取最後一個匹配（通常是最終答案）
                json_str = matches[-1] if isinstance(matches[-1], str) else matches[-1]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    continue

        # 無法解析 JSON
        raise AgentError(
            "Failed to parse JSON from agent response",
            retryable=False,
            details={"raw_output": output[:500]},
        )


class ParallelAgentCaller:
    """並行 Agent 調用器"""

    def __init__(self, caller: Optional[AgentCaller] = None):
        """
        初始化並行調用器

        Args:
            caller: 基礎調用器（可選）
        """
        self.caller = caller or AgentCaller()

    def call_parallel(
        self,
        agents: List[Dict],
        context: Optional[Dict] = None,
    ) -> Dict[str, AgentResponse]:
        """
        並行調用多個 Agent

        Args:
            agents: Agent 配置列表，每個包含 id, prompt, model (可選)
            context: 共享上下文

        Returns:
            以 agent_id 為 key 的結果字典
        """
        import concurrent.futures

        results = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(agents)) as executor:
            # 提交所有任務
            future_to_agent = {}
            for agent in agents:
                future = executor.submit(
                    self.caller.call,
                    prompt=agent["prompt"],
                    model=agent.get("model"),
                    context=context,
                )
                future_to_agent[future] = agent["id"]

            # 收集結果
            for future in concurrent.futures.as_completed(future_to_agent):
                agent_id = future_to_agent[future]
                try:
                    results[agent_id] = future.result()
                except Exception as e:
                    results[agent_id] = AgentResponse(
                        success=False,
                        error=str(e),
                    )

        return results


# 全域實例
_caller: Optional[AgentCaller] = None
_parallel_caller: Optional[ParallelAgentCaller] = None


def get_caller(
    model: str = "sonnet",
    timeout: int = 300,
) -> AgentCaller:
    """取得 Agent 調用器"""
    global _caller
    if _caller is None:
        _caller = AgentCaller(default_model=model, timeout=timeout)
    return _caller


def get_parallel_caller() -> ParallelAgentCaller:
    """取得並行調用器"""
    global _parallel_caller
    if _parallel_caller is None:
        _parallel_caller = ParallelAgentCaller(get_caller())
    return _parallel_caller
