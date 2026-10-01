# 动态规划式异构多智能体系统

基于 Planner Agent 与 DAG Workflow 的城市应急智能决策应用。

系统不由单一 LLM 直接生成完整答案，而是让 LLM 作为 **Planner Agent** 理解任务、动态生成任务 DAG，再由多个异构 Agent 按依赖关系并行执行、最终融合为综合决策：

```text
User Task
  -> Planner Agent（任务规划，生成 DAG）
  -> DAGExecutor（按依赖调度）
  -> Weather / Traffic / Resource Agents（异构协同）
  -> Reflection Agent（结果融合）
  -> Final Decision
```

## 核心特性

- **动态任务规划**：Planner Agent 根据任务动态生成执行计划，而非固定流程
- **异构 Agent 协同**：天气分析、交通评估、资源调度等多个领域 Agent 分工协作
- **执行过程可解释**：DAG 节点状态实时可见，决策链路一目了然
- **跨领域迁移**：同一框架可迁移至新能源充电规划等不同场景

## 快速开始

### 环境要求

- Python 3.10+（推荐 3.12）
- [uv](https://docs.astral.sh/uv/)（可选，脚本依赖它自动管理环境）
- 一个 OpenAI 兼容的 LLM API Key

### 运行 Demo

```bash
cp .env.example .env   # 填入你的 LLM_API_KEY
./run_demo.sh
```

然后打开 <http://localhost:8080>。

Demo 默认使用离线静态结果保证演示稳定；在界面中打开"在线调用 LLM"开关即可使用真实 Planner 与 Agent 链路执行。

### 运行测试

```bash
./run_tests.sh
# 或手动执行
python -m pytest tests/ -v
```

## 项目结构

```text
magents/
├── configs/               # Agent 与场景配置
├── demo/scenarios/        # 演示场景数据
├── src/
│   ├── agents/            # Planner / Weather / Traffic / Resource / Reflection Agent
│   ├── demo/              # NiceGUI 交互界面
│   ├── environment/       # 环境模拟器
│   ├── llm/               # LLM 客户端封装
│   └── workflow/          # DAG 数据结构与执行器
├── run_demo.sh            # 一键启动 Demo
└── run_tests.sh           # 一键运行测试
```

## 主场景

深圳南山区科技园周边暴雨应急决策：根据持续强降雨、主干道拥堵、救援资源分布等信息，系统输出路段封控、救援调度、区域预警与绕行建议的综合决策方案。
