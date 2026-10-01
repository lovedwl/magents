"""
TrafficAgent - 交通评估智能体
负责交通流量分析和影响评估
"""

from typing import Dict, Any, Optional
from .base_agent import BaseAgent, AgentResult
from ..llm.llm_client import get_llm_client

TRAFFIC_SYSTEM_PROMPT = """你是一个专业的交通分析专家。你的职责是：
1. 分析交通流量和道路状况
2. 评估事件对交通的影响
3. 识别交通瓶颈和风险点
4. 提供交通疏导和管控建议

你需要基于提供的任务信息，给出专业的交通分析报告。

输出格式要求：
- 影响范围
- 受影响路段
- 拥堵程度评估
- 疏导建议
- 应急通道规划"""


class TrafficAgent(BaseAgent):
    """
    交通评估智能体

    负责交通流量分析和影响评估。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="Traffic Agent",
            description="交通流量分析与影响评估",
            config=config,
        )
        self.llm = get_llm_client()

    async def execute(self, task: str, context: Dict[str, Any] = None) -> AgentResult:
        """
        执行交通分析

        Args:
            task: 交通分析任务
            context: 上下文信息

        Returns:
            AgentResult: 交通分析结果
        """
        try:
            # 构建提示词
            prompt = f"""请对以下任务进行交通分析：

任务：{task}

请提供详细的交通分析报告。"""

            if context:
                prompt += f"\n\n相关上下文信息：\n{context}"

            # 调用 LLM
            messages = [
                {"role": "system", "content": TRAFFIC_SYSTEM_PROMPT},
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
        """解析交通分析结果"""
        return {
            "raw_analysis": response,
            "impact_level": self._extract_impact_level(response),
        }

    def _extract_impact_level(self, text: str) -> str:
        """提取影响程度"""
        if "严重" in text or "重大" in text:
            return "严重"
        elif "较大" in text or "显著" in text:
            return "较大"
        elif "一般" in text or "中等" in text:
            return "一般"
        else:
            return "轻微"
