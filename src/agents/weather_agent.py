"""
WeatherAgent - 天气分析智能体
负责气象数据分析和风险评估
"""

from typing import Dict, Any, Optional
from .base_agent import BaseAgent, AgentResult
from ..llm.llm_client import get_llm_client

WEATHER_SYSTEM_PROMPT = """你是一个专业的气象分析专家。你的职责是：
1. 分析天气状况和气象数据
2. 评估天气风险等级
3. 预测天气变化趋势
4. 提供气象相关的决策建议

你需要基于提供的任务信息，给出专业的天气分析报告。

输出格式要求：
- 风险等级：低/中/高/极高
- 当前天气状况
- 未来趋势预测
- 对任务的影响分析
- 应对建议"""


class WeatherAgent(BaseAgent):
    """
    天气分析智能体

    负责气象数据分析和风险评估。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="Weather Agent",
            description="天气分析与风险评估",
            config=config,
        )
        self.llm = get_llm_client()

    async def execute(self, task: str, context: Dict[str, Any] = None) -> AgentResult:
        """
        执行天气分析

        Args:
            task: 天气分析任务
            context: 上下文信息

        Returns:
            AgentResult: 天气分析结果
        """
        try:
            # 构建提示词
            prompt = f"""请对以下任务进行天气分析：

任务：{task}

请提供详细的天气分析报告。"""

            if context:
                prompt += f"\n\n相关上下文信息：\n{context}"

            # 调用 LLM
            messages = [
                {"role": "system", "content": WEATHER_SYSTEM_PROMPT},
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
        """解析天气分析结果"""
        return {
            "raw_analysis": response,
            "risk_level": self._extract_risk_level(response),
        }

    def _extract_risk_level(self, text: str) -> str:
        """提取风险等级"""
        text_lower = text.lower()
        if "极高" in text or "extreme" in text_lower:
            return "极高"
        elif "高" in text or "high" in text_lower:
            return "高"
        elif "中" in text or "medium" in text_lower:
            return "中"
        else:
            return "低"
