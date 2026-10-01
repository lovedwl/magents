#!/bin/bash
# 启动演示脚本

echo "=========================================="
echo "动态规划式异构多智能体系统"
echo "=========================================="

# 检查 uv
if ! command -v uv &> /dev/null; then
    echo "错误: 未安装 uv"
    echo "请运行: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# 创建虚拟环境（如果不存在）
if [ ! -d ".venv" ]; then
    echo "创建虚拟环境 (Python 3.12)..."
    uv venv --python 3.12 .venv
fi

# 安装依赖
echo "安装依赖..."
uv pip install pydantic openai python-dotenv pyyaml nicegui

# 加载环境变量
if [ -f ".env" ]; then
    set -a
    source <(grep -v '^#' .env | grep -v '^$')
    set +a
fi

# 启动 NiceGUI
echo "启动演示界面 (http://localhost:8080)..."
.venv/bin/python src/demo/web_demo.py
