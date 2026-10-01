"""
LLMClient - 大语言模型客户端
封装 OpenAI 兼容 API 调用
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from openai import AsyncOpenAI
from dotenv import load_dotenv

# 查找项目根目录的 .env 文件
_project_root = Path(__file__).parent.parent.parent
_env_path = _project_root / ".env"
load_dotenv(_env_path)


class LLMClient:
    """
    LLM 客户端

    支持 OpenAI 兼容的 API（如 DeepSeek）
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ):
        """
        初始化 LLM 客户端

        Args:
            api_key: API 密钥，默认从环境变量读取
            base_url: API 基础 URL
            model: 模型名称，默认从环境变量读取
            temperature: 温度参数
            max_tokens: 最大 token 数
        """
        self.api_key = api_key or os.getenv("LLM_API_KEY", "")
        self.base_url = base_url or os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
        self.model = model or os.getenv("LLM_MODEL", "deepseek-chat")
        self.temperature = temperature
        self.max_tokens = max_tokens

        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        发送聊天请求

        Args:
            messages: 消息列表，格式 [{"role": "user", "content": "..."}]
            model: 模型名称，覆盖默认值
            temperature: 温度参数，覆盖默认值
            max_tokens: 最大 token 数，覆盖默认值

        Returns:
            str: 模型回复内容
        """
        response = await self.client.chat.completions.create(
            model=model or self.model,
            messages=messages,
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens,
        )
        return response.choices[0].message.content

    async def complete(self, prompt: str, **kwargs) -> str:
        """
        简单补全接口

        Args:
            prompt: 用户输入
            **kwargs: 其他参数

        Returns:
            str: 模型回复
        """
        messages = [{"role": "user", "content": prompt}]
        return await self.chat(messages, **kwargs)


# 全局默认客户端
_default_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """获取全局 LLM 客户端"""
    global _default_client
    if _default_client is None:
        _default_client = LLMClient()
    return _default_client
