#!/bin/bash
# 运行测试脚本

echo "=========================================="
echo "运行测试"
echo "=========================================="

# 检查 uv
if ! command -v uv &> /dev/null; then
    echo "错误: 未安装 uv"
    exit 1
fi

# 创建虚拟环境（如果不存在）
if [ ! -d ".venv" ]; then
    echo "创建虚拟环境 (Python 3.12)..."
    uv venv --python 3.12 .venv
fi

# 安装依赖
echo "安装依赖..."
uv pip install pydantic openai python-dotenv pyyaml pytest pytest-asyncio

# 加载 .env 配置
if [ -f ".env" ]; then
    set -a
    source <(grep -v '^#' .env | grep -v '^$')
    set +a
fi

# 运行测试
echo "运行测试..."
.venv/bin/python -m pytest tests/ -v

echo ""
echo "测试完成！"
