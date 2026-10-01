"""
ReflectionAgent - 结果融合智能体
负责汇总各 Agent 输出并生成最终决策报告
"""

from typing import Dict, Any, Optional
from .base_agent import BaseAgent, AgentResult
from ..llm.llm_client import get_llm_client

REFLECTION_SYSTEM_PROMPT = """你是一个决策分析专家。你的职责是：
1. 汇总多个专业 Agent 的分析结果
2. 评估各方案的优劣
3. 识别潜在风险和冲突
4. 生成综合决策报告

你需要基于提供的各 Agent 分析结果，生成最终的决策方案。

输出格式要求：
- 情况概述
- 各领域分析摘要
- 综合评估
- 最终决策方案
- 执行步骤
- 风险提示"""


class ReflectionAgent(BaseAgent):
    """
    结果融合智能体

    汇总各 Agent 输出，生成最终决策报告。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="Reflection Agent",
            description="结果融合与决策生成",
            config=config,
        )
        self.llm = get_llm_client()

    async def execute(self, task: str, context: Dict[str, Any] = None) -> AgentResult:
        """
        执行结果融合

        Args:
            task: 原始任务描述
            context: 其他 Agent 的分析结果

        Returns:
            AgentResult: 最终决策报告
        """
        try:
            # 构建提示词
            prompt = f"""请基于以下信息生成最终决策报告：

原始任务：{task}

各领域分析结果：
"""

            if context:
                for agent_name, result in context.items():
                    if isinstance(result, dict) and "raw_analysis" in result:
                        prompt += f"\n### {agent_name}:\n{result['raw_analysis']}\n"
                    else:
                        prompt += f"\n### {agent_name}:\n{result}\n"

            prompt += "\n请生成综合决策报告。"

            # 调用 LLM
            messages = [
                {"role": "system", "content": REFLECTION_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ]

            response = await self.llm.chat(messages, max_tokens=3000)

            # 解析结果
            report = self._parse_report(response)

            return AgentResult(
                agent_name=self.name,
                success=True,
                output=report,
            )

        except Exception as e:
            return AgentResult(
                agent_name=self.name,
                success=False,
                output=None,
                error=str(e),
            )

    def _parse_report(self, response: str) -> Dict[str, Any]:
        """解析决策报告"""
        return {
            "raw_report": response,
            "summary": self._extract_summary(response),
        }

    def _extract_summary(self, text: str) -> str:
        """提取摘要"""
        # 提取前 500 字作为摘要
        if len(text) > 500:
            return text[:500] + "..."
        return text
