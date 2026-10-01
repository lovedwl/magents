"""
Executor 测试
"""

import pytest
import asyncio
from src.workflow.dag import DAG, DAGNode
from src.workflow.executor import DAGExecutor
from src.agents.base_agent import BaseAgent, AgentResult


class MockAgent(BaseAgent):
    """模拟 Agent，用于测试"""

    def __init__(self, name: str, output: str = "mock output"):
        super().__init__(name=name, description=f"Mock {name}")
        self.output = output

    async def execute(self, task: str, context: dict = None) -> AgentResult:
        return AgentResult(
            agent_name=self.name,
            success=True,
            output=self.output,
        )


def test_executor_creation():
    """测试执行器创建"""
    agents = {"weather": MockAgent("weather")}
    executor = DAGExecutor(agents)
    assert executor.agents == agents


def test_executor_linear_dag():
    """测试线性 DAG 执行"""
    async def run():
        # 创建模拟 Agent
        agents = {
            "weather": MockAgent("weather", "天气分析结果"),
            "traffic": MockAgent("traffic", "交通分析结果"),
            "reflection": MockAgent("reflection", "最终报告"),
        }

        # 创建线性 DAG
        dag = DAG()
        dag.add_node(DAGNode(id="w1", agent_type="weather", task="天气"))
        dag.add_node(DAGNode(id="t1", agent_type="traffic", task="交通"))
        dag.add_node(DAGNode(id="r1", agent_type="reflection", task="融合"))

        dag.add_edge("w1", "r1")
        dag.add_edge("t1", "r1")

        # 执行
        executor = DAGExecutor(agents)
        results = await executor.execute(dag)

        # 验证
        assert len(results) == 3
        assert results["w1"].success is True
        assert results["t1"].success is True
        assert results["r1"].success is True

    asyncio.run(run())


def test_executor_callback():
    """测试执行器回调"""
    async def run():
        agents = {
            "weather": MockAgent("weather", "天气分析结果"),
        }

        dag = DAG()
        dag.add_node(DAGNode(id="w1", agent_type="weather", task="天气"))

        executor = DAGExecutor(agents)

        # 记录回调
        callback_log = []

        def on_complete(node, result):
            callback_log.append({
                "node_id": node.id,
                "success": result.success,
            })

        executor.on_node_complete(on_complete)

        await executor.execute(dag)

        # 验证回调被调用
        assert len(callback_log) == 1
        assert callback_log[0]["node_id"] == "w1"
        assert callback_log[0]["success"] is True

    asyncio.run(run())


def test_executor_missing_agent():
    """测试缺少 Agent 的情况"""
    async def run():
        agents = {}  # 空的 agent 字典

        dag = DAG()
        dag.add_node(DAGNode(id="w1", agent_type="weather", task="天气"))

        executor = DAGExecutor(agents)
        results = await executor.execute(dag)

        # 应该失败
        assert results["w1"].success is False
        assert "未找到 Agent 类型" in results["w1"].error

    asyncio.run(run())
