"""
DAG 测试
"""

import pytest
from src.workflow.dag import DAG, DAGNode, NodeStatus


def test_dag_creation():
    """测试 DAG 创建"""
    dag = DAG()
    assert len(dag.nodes) == 0
    assert len(dag.edges) == 0


def test_add_node():
    """测试添加节点"""
    dag = DAG()
    node = DAGNode(id="node1", agent_type="weather", task="分析天气")
    dag.add_node(node)

    assert "node1" in dag.nodes
    assert dag.nodes["node1"].agent_type == "weather"


def test_add_edge():
    """测试添加边"""
    dag = DAG()
    node1 = DAGNode(id="node1", agent_type="weather", task="分析天气")
    node2 = DAGNode(id="node2", agent_type="traffic", task="评估交通")

    dag.add_node(node1)
    dag.add_node(node2)
    dag.add_edge("node1", "node2")

    assert len(dag.edges) == 1
    assert dag.edges[0].source == "node1"
    assert dag.edges[0].target == "node2"
    assert "node1" in dag.get_dependencies("node2")


def test_topological_sort():
    """测试拓扑排序"""
    dag = DAG()

    # 创建线性 DAG: node1 -> node2 -> node3
    dag.add_node(DAGNode(id="node1", agent_type="weather", task="天气"))
    dag.add_node(DAGNode(id="node2", agent_type="traffic", task="交通"))
    dag.add_node(DAGNode(id="node3", agent_type="reflection", task="融合"))

    dag.add_edge("node1", "node2")
    dag.add_edge("node2", "node3")

    order = dag.topological_sort()
    assert order == ["node1", "node2", "node3"]


def test_topological_sort_parallel():
    """测试并行节点的拓扑排序"""
    dag = DAG()

    # 创建并行 DAG: node1, node2 -> node3
    dag.add_node(DAGNode(id="node1", agent_type="weather", task="天气"))
    dag.add_node(DAGNode(id="node2", agent_type="traffic", task="交通"))
    dag.add_node(DAGNode(id="node3", agent_type="reflection", task="融合"))

    dag.add_edge("node1", "node3")
    dag.add_edge("node2", "node3")

    order = dag.topological_sort()
    # node1 和 node2 可以并行，node3 必须在最后
    assert order.index("node1") < order.index("node3")
    assert order.index("node2") < order.index("node3")


def test_circular_dependency():
    """测试循环依赖检测"""
    dag = DAG()

    dag.add_node(DAGNode(id="node1", agent_type="a", task="A"))
    dag.add_node(DAGNode(id="node2", agent_type="b", task="B"))

    dag.add_edge("node1", "node2")
    dag.add_edge("node2", "node1")  # 循环

    with pytest.raises(ValueError, match="循环依赖"):
        dag.topological_sort()


def test_get_ready_nodes():
    """测试获取可执行节点"""
    dag = DAG()

    dag.add_node(DAGNode(id="node1", agent_type="weather", task="天气"))
    dag.add_node(DAGNode(id="node2", agent_type="traffic", task="交通"))
    dag.add_node(DAGNode(id="node3", agent_type="reflection", task="融合"))

    dag.add_edge("node1", "node3")
    dag.add_edge("node2", "node3")

    # 初始状态，node1 和 node2 应该是可执行的
    ready = dag.get_ready_nodes()
    ready_ids = [n.id for n in ready]
    assert "node1" in ready_ids
    assert "node2" in ready_ids
    assert "node3" not in ready_ids

    # 完成 node1 后
    dag.nodes["node1"].status = NodeStatus.COMPLETED
    ready = dag.get_ready_nodes()
    ready_ids = [n.id for n in ready]
    assert "node1" not in ready_ids
    assert "node2" in ready_ids
    assert "node3" not in ready_ids  # node2 还没完成

    # 完成 node2 后
    dag.nodes["node2"].status = NodeStatus.COMPLETED
    ready = dag.get_ready_nodes()
    ready_ids = [n.id for n in ready]
    assert "node3" in ready_ids


def test_is_complete():
    """测试完成检查"""
    dag = DAG()

    dag.add_node(DAGNode(id="node1", agent_type="weather", task="天气"))
    dag.add_node(DAGNode(id="node2", agent_type="traffic", task="交通"))

    assert not dag.is_complete()

    dag.nodes["node1"].status = NodeStatus.COMPLETED
    assert not dag.is_complete()

    dag.nodes["node2"].status = NodeStatus.COMPLETED
    assert dag.is_complete()


def test_dag_serialization():
    """测试 DAG 序列化"""
    dag = DAG()

    dag.add_node(DAGNode(id="node1", agent_type="weather", task="天气"))
    dag.add_node(DAGNode(id="node2", agent_type="traffic", task="交通"))
    dag.add_edge("node1", "node2")

    # 序列化
    data = dag.to_dict()
    assert len(data["nodes"]) == 2
    assert len(data["edges"]) == 1

    # 反序列化
    dag2 = DAG.from_dict(data)
    assert len(dag2.nodes) == 2
    assert len(dag2.edges) == 1
    assert "node1" in dag2.get_dependencies("node2")
