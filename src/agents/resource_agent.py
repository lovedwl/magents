"""
ResourceAgent - 资源调配智能体
负责应急资源分配和优化
"""

from typing import Dict, Any, Optional
from .base_agent import BaseAgent, AgentResult
from ..llm.llm_client import get_llm_client

RESOURCE_SYSTEM_PROMPT = """你是一个专业的资源调配专家。你的职责是：
1. 分析资源需求
2. 评估现有资源库存
3. 制定资源调配方案
4. 优化资源分配策略

你需要基于提供的任务信息，给出专业的资源调配方案。

输出格式要求：
- 资源需求清单
- 现有资源评估
- 调配方案
- 优先级排序
- 时间安排"""


class ResourceAgent(BaseAgent):
    """
    资源调配智能体

    负责应急资源分配和优化。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="Resource Agent",
            description="应急资源调配与优化",
            config=config,
        )
        self.llm = get_llm_client()

    async def execute(self, task: str, context: Dict[str, Any] = None) -> AgentResult:
        """
        执行资源调配分析

        Args:
            task: 资源调配任务
            context: 上下文信息

        Returns:
            AgentResult: 资源调配结果
        """
        try:
            # 构建提示词
            prompt = f"""请对以下任务进行资源调配分析：

任务：{task}

请提供详细的资源调配方案。"""

            if context:
                prompt += f"\n\n相关上下文信息：\n{context}"

            # 调用 LLM
            messages = [
                {"role": "system", "content": RESOURCE_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ]

            response = await self.llm.chat(messages)

            # 解析结果
            analysis = self._parse_analysis(response)

            return AgentResult(
                agent_name=self.name,
                success=True,
                output=analysis,
            )

        except Exception as e:
            return AgentResult(
                agent_name=self.name,
                success=False,
                output=None,
                error=str(e),
            )

    def _parse_analysis(self, response: str) -> Dict[str, Any]:
        """解析资源调配结果"""
        return {
            "raw_analysis": response,
            "resource_type": self._extract_resource_type(response),
        }

    def _extract_resource_type(self, text: str) -> str:
        """提取资源类型"""
        if "人力" in text or "人员" in text:
            return "人力资源"
        elif "物资" in text or "设备" in text:
            return "物资设备"
        elif "资金" in text or "预算" in text:
            return "资金"
        else:
            return "综合资源"
