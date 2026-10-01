"""
Agent 测试
"""

import pytest
import asyncio
from src.agents.base_agent import BaseAgent, AgentResult


def test_base_agent_interface():
    """测试 BaseAgent 接口"""
    # BaseAgent 是抽象类，不能直接实例化
    with pytest.raises(TypeError):
        BaseAgent("test", "test agent")


def test_agent_result():
    """测试 AgentResult 数据结构"""
    result = AgentResult(
        agent_name="TestAgent",
        success=True,
        output={"key": "value"},
    )

    assert result.agent_name == "TestAgent"
    assert result.success is True
    assert result.output == {"key": "value"}
    assert result.error is None


def test_agent_result_with_error():
    """测试带错误的 AgentResult"""
    result = AgentResult(
        agent_name="TestAgent",
        success=False,
        output=None,
        error="Something went wrong",
    )

    assert result.success is False
    assert result.error == "Something went wrong"


# 以下测试需要 LLM API，标记为跳过
@pytest.mark.skip(reason="需要 LLM API 配置")
def test_planner_agent():
    """测试 PlannerAgent"""
    from src.agents.planner_agent import PlannerAgent

    async def run():
        planner = PlannerAgent()
        result = await planner.execute("某城市突发暴雨，请制定应急响应方案。")
        assert result.success is True
        assert "nodes" in result.output

    asyncio.run(run())


@pytest.mark.skip(reason="需要 LLM API 配置")
def test_weather_agent():
    """测试 WeatherAgent"""
    from src.agents.weather_agent import WeatherAgent

    async def run():
        agent = WeatherAgent()
        result = await agent.execute("分析暴雨天气对城市的影响")
        assert result.success is True
        assert "raw_analysis" in result.output

    asyncio.run(run())
