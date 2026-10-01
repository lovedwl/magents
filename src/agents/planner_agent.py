"""
PlannerAgent - 任务规划智能体
负责理解用户需求、拆解任务、生成 DAG 工作流
"""

import json
from typing import Dict, Any, Optional
from .base_agent import BaseAgent, AgentResult
from ..workflow.dag import DAG, DAGNode
from ..llm.llm_client import get_llm_client

# Planner 系统提示词
PLANNER_SYSTEM_PROMPT = """你是一个任务规划专家。你的职责是：
1. 理解用户的复杂任务需求
2. 将任务拆解为多个子任务
3. 分析子任务之间的依赖关系
4. 生成 DAG（有向无环图）工作流

你需要输出一个 JSON 格式的 DAG 定义，包含：
- nodes: 节点列表，每个节点包含 id, agent_type, task
- edges: 边列表，每条边包含 source, target

可用的 Agent 类型：
- weather: 天气分析
- traffic: 交通评估
- resource: 资源调配
- reflection: 结果融合（通常是最后一个节点）

输出格式示例：
```json
{
  "nodes": [
    {"id": "weather_1", "agent_type": "weather", "task": "分析天气状况"},
    {"id": "traffic_1", "agent_type": "traffic", "task": "评估交通影响"},
    {"id": "resource_1", "agent_type": "resource", "task": "调配应急资源"},
    {"id": "reflection_1", "agent_type": "reflection", "task": "融合结果生成方案"}
  ],
  "edges": [
    {"source": "weather_1", "target": "reflection_1"},
    {"source": "traffic_1", "target": "reflection_1"},
    {"source": "resource_1", "target": "reflection_1"}
  ]
}
```

注意：
- reflection 节点必须依赖其他所有分析节点
- 如果任务不需要某个 Agent，可以不包含
- 输出纯 JSON，不要包含其他文字"""


class PlannerAgent(BaseAgent):
    """
    任务规划智能体

    接收用户自然语言任务，输出 DAG 工作流定义。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="Planner Agent",
            description="任务规划与调度智能体",
            config=config,
        )
        self.llm = get_llm_client()

    async def execute(self, task: str, context: Dict[str, Any] = None) -> AgentResult:
        """
        执行任务规划

        Args:
            task: 用户任务描述
            context: 上下文（Planner 通常不需要）

        Returns:
            AgentResult: 包含 DAG 定义的结果
        """
        try:
            # 构建提示词
            prompt = f"""请分析以下任务，并生成 DAG 工作流定义：

任务：{task}

请输出 JSON 格式的 DAG 定义。"""

            # 调用 LLM
            messages = [
                {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ]

            response = await self.llm.chat(messages)

            # 解析 JSON
            dag_data = self._parse_dag_json(response)

            # 验证并构建 DAG
            dag = DAG.from_dict(dag_data)

            return AgentResult(
                agent_name=self.name,
                success=True,
                output=dag_data,
                metadata={"dag": dag.to_dict()},
            )

        except Exception as e:
            return AgentResult(
                agent_name=self.name,
                success=False,
                output=None,
                error=str(e),
            )

    def _parse_dag_json(self, response: str) -> Dict[str, Any]:
        """从 LLM 响应中解析 JSON"""
        # 尝试直接解析
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # 尝试从 markdown 代码块中提取
        import re
        json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        raise ValueError(f"无法解析 LLM 输出为 JSON: {response[:200]}...")
