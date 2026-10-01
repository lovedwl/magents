"""
BaseAgent - 智能体基类
所有 Agent 的抽象基类，定义统一接口
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel


class AgentResult(BaseModel):
    """Agent 执行结果"""
    agent_name: str
    success: bool
    output: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}


class BaseAgent(ABC):
    """
    智能体基类

    所有领域 Agent 和系统 Agent 都应继承此类，
    并实现 execute 方法。
    """

    def __init__(self, name: str, description: str, config: Optional[Dict[str, Any]] = None):
        """
        初始化 Agent

        Args:
            name: Agent 名称
            description: Agent 描述
            config: 配置参数
        """
        self.name = name
        self.description = description
        self.config = config or {}

    @abstractmethod
    async def execute(self, task: str, context: Dict[str, Any] = None) -> AgentResult:
        """
        执行任务

        Args:
            task: 任务描述
            context: 上下文信息（其他 Agent 的输出等）

        Returns:
            AgentResult: 执行结果
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
