"""
DAGExecutor - DAG 执行引擎
负责按照 DAG 依赖顺序调度 Agent 执行
"""

import asyncio
from typing import Dict, Any, Optional, Callable, List
from .dag import DAG, DAGNode, NodeStatus
from ..agents.base_agent import BaseAgent, AgentResult


class DAGExecutor:
    """
    DAG 执行引擎

    按照拓扑顺序执行 DAG 中的节点，支持并行执行无依赖的节点。
    """

    def __init__(self, agents: Dict[str, BaseAgent]):
        """
        初始化执行器

        Args:
            agents: Agent 字典，key 为 agent_type，value 为 Agent 实例
        """
        self.agents = agents
        self.results: Dict[str, AgentResult] = {}
        self._on_start_callbacks: List[Callable] = []
        self._on_complete_callbacks: List[Callable] = []

    def on_node_start(self, callback: Callable[[DAGNode], None]):
        """注册节点开始回调"""
        self._on_start_callbacks.append(callback)

    def on_node_complete(self, callback: Callable[[DAGNode, AgentResult], None]):
        """注册节点完成回调"""
        self._on_complete_callbacks.append(callback)

    async def execute(self, dag: DAG) -> Dict[str, AgentResult]:
        """
        执行 DAG

        Args:
            dag: 要执行的 DAG

        Returns:
            Dict[str, AgentResult]: 所有节点的执行结果
        """
        self.results = {}

        while not dag.is_complete():
            # 获取可执行的节点
            ready_nodes = dag.get_ready_nodes()

            if not ready_nodes:
                # 没有可执行节点且未完成，说明有循环或错误
                pending = [n for n in dag.nodes.values() if n.status == NodeStatus.PENDING]
                if pending:
                    raise RuntimeError(f"无法继续执行，存在阻塞节点: {[n.id for n in pending]}")
                break

            # 并行执行所有可执行节点
            tasks = [self._execute_node(node) for node in ready_nodes]
            await asyncio.gather(*tasks)

        return self.results

    async def _execute_node(self, node: DAGNode) -> None:
        """执行单个节点"""
        node.status = NodeStatus.RUNNING

        # 触发开始回调
        for callback in self._on_start_callbacks:
            callback(node)

        try:
            # 获取对应的 Agent
            agent = self.agents.get(node.agent_type)
            if not agent:
                raise ValueError(f"未找到 Agent 类型: {node.agent_type}")

            # 收集依赖节点的结果作为上下文
            context = self._build_context(node)

            # 执行 Agent
            result = await agent.execute(node.task, context)

            # 更新状态
            node.status = NodeStatus.COMPLETED
            node.result = result.output
            self.results[node.id] = result

            # 触发完成回调
            for callback in self._on_complete_callbacks:
                callback(node, result)

        except Exception as e:
            node.status = NodeStatus.FAILED
            node.error = str(e)
            error_result = AgentResult(
                agent_name=node.agent_type,
                success=False,
                output=None,
                error=str(e),
            )
            self.results[node.id] = error_result
            for callback in self._on_complete_callbacks:
                callback(node, error_result)

    def _build_context(self, node: DAGNode) -> Dict[str, Any]:
        """构建节点执行上下文"""
        context = {}
        for dep_id in node.dependencies:
            if dep_id in self.results:
                context[dep_id] = self.results[dep_id].output
        return context
