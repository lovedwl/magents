"""
DAG - 有向无环图数据结构
用于表示任务依赖关系
"""

from typing import Dict, List, Optional, Set, Any
from pydantic import BaseModel, Field
from enum import Enum


class NodeStatus(str, Enum):
    """节点状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class DAGNode(BaseModel):
    """DAG 节点"""
    model_config = {"use_enum_values": True}

    id: str
    agent_type: str
    task: str
    dependencies: List[str] = Field(default_factory=list)
    status: NodeStatus = NodeStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None


class DAGEdge(BaseModel):
    """DAG 边"""
    source: str
    target: str


class DAG:
    """
    有向无环图

    管理任务节点和依赖关系，支持拓扑排序和执行调度。
    """

    def __init__(self):
        self.nodes: Dict[str, DAGNode] = {}
        self.edges: List[DAGEdge] = []
        self._adjacency: Dict[str, List[str]] = {}  # 邻接表
        self._reverse_adjacency: Dict[str, List[str]] = {}  # 反向邻接表

    def add_node(self, node: DAGNode) -> None:
        """添加节点"""
        self.nodes[node.id] = node
        if node.id not in self._adjacency:
            self._adjacency[node.id] = []
        if node.id not in self._reverse_adjacency:
            self._reverse_adjacency[node.id] = []

    def add_edge(self, source: str, target: str) -> None:
        """添加边（source -> target）"""
        if source not in self.nodes or target not in self.nodes:
            raise ValueError(f"节点不存在: {source} 或 {target}")

        edge = DAGEdge(source=source, target=target)
        self.edges.append(edge)

        self._adjacency.setdefault(source, []).append(target)
        self._reverse_adjacency.setdefault(target, []).append(source)

        # 更新目标节点的依赖
        if source not in self.nodes[target].dependencies:
            self.nodes[target].dependencies.append(source)

    def get_dependencies(self, node_id: str) -> List[str]:
        """获取节点的所有依赖"""
        return self._reverse_adjacency.get(node_id, [])

    def get_dependents(self, node_id: str) -> List[str]:
        """获取依赖此节点的所有节点"""
        return self._adjacency.get(node_id, [])

    def get_ready_nodes(self) -> List[DAGNode]:
        """获取所有可执行的节点（依赖已完成）"""
        ready = []
        for node in self.nodes.values():
            if node.status != NodeStatus.PENDING:
                continue

            # 检查所有依赖是否已完成
            deps = self.get_dependencies(node.id)
            all_deps_completed = all(
                self.nodes[dep].status == NodeStatus.COMPLETED
                for dep in deps
            )

            if all_deps_completed:
                ready.append(node)

        return ready

    def topological_sort(self) -> List[str]:
        """
        拓扑排序

        Returns:
            List[str]: 节点 ID 的拓扑顺序
        """
        # 计算入度
        in_degree = {node_id: 0 for node_id in self.nodes}
        for node_id in self.nodes:
            for dep in self.get_dependencies(node_id):
                in_degree[node_id] += 1

        # 找出入度为 0 的节点
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            node_id = queue.pop(0)
            result.append(node_id)

            # 更新依赖此节点的入度
            for dependent in self.get_dependents(node_id):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        if len(result) != len(self.nodes):
            raise ValueError("DAG 中存在循环依赖")

        return result

    def is_complete(self) -> bool:
        """检查所有节点是否完成"""
        return all(
            node.status in [NodeStatus.COMPLETED, NodeStatus.FAILED]
            for node in self.nodes.values()
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "nodes": [node.model_dump() for node in self.nodes.values()],
            "edges": [{"source": e.source, "target": e.target} for e in self.edges],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DAG":
        """从字典创建 DAG"""
        dag = cls()

        for node_data in data.get("nodes", []):
            node = DAGNode(**node_data)
            dag.add_node(node)

        for edge_data in data.get("edges", []):
            dag.add_edge(edge_data["source"], edge_data["target"])

        return dag
