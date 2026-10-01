"""
NiceGUI 演示界面
动态规划式异构多智能体系统
"""

import asyncio
from nicegui import ui, app
from typing import Dict, Any, Optional

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.agents.planner_agent import PlannerAgent
from src.agents.weather_agent import WeatherAgent
from src.agents.traffic_agent import TrafficAgent
from src.agents.resource_agent import ResourceAgent
from src.agents.reflection_agent import ReflectionAgent
from src.workflow.dag import DAG, DAGNode, NodeStatus
from src.workflow.executor import DAGExecutor


# ── 常量 ──────────────────────────────────────────────────
AGENT_META = {
    "weather":    {"label": "天气分析", "icon": "🌦️", "color": "#3b82f6"},
    "traffic":    {"label": "交通评估", "icon": "🚗", "color": "#8b5cf6"},
    "resource":   {"label": "资源调配", "icon": "📦", "color": "#f59e0b"},
    "reflection": {"label": "决策融合", "icon": "📋", "color": "#10b981"},
}

STATUS_STYLE = {
    "pending":   {"border": "#94a3b8", "bg": "#f8fafc", "text": "#64748b"},
    "running":   {"border": "#3b82f6", "bg": "#dbeafe", "text": "#1d4ed8"},
    "completed": {"border": "#22c55e", "bg": "#dcfce7", "text": "#15803d"},
    "failed":    {"border": "#ef4444", "bg": "#fee2e2", "text": "#dc2626"},
}


def get_meta(agent_type: str) -> dict:
    return AGENT_META.get(agent_type, {"label": agent_type, "icon": "⚙️", "color": "#6b7280"})


# ── 应用状态 ──────────────────────────────────────────────
class AppState:
    def __init__(self):
        self.dag_data: Optional[Dict] = None
        self.results: Dict[str, Any] = {}
        self.node_status: Dict[str, str] = {}
        self.selected_node: Optional[str] = None

    def reset(self):
        self.dag_data = None
        self.results = {}
        self.node_status = {}
        self.selected_node = None


state = AppState()


# ── vis.js DAG 渲染 ──────────────────────────────────────
def build_vis_data(dag_data: Dict) -> Dict:
    """构建 vis.js 数据"""
    nodes = []
    for nd in dag_data.get("nodes", []):
        nid = nd["id"]
        agent_type = nd.get("agent_type", "")
        meta = get_meta(agent_type)
        status = state.node_status.get(nid, "pending")
        s = STATUS_STYLE[status]

        short_task = nd.get("task", "")[:20]
        label = f"{meta['icon']} {meta['label']}\n{short_task}"

        nodes.append({
            "id": nid,
            "label": label,
            "shape": "box",
            "color": {"border": s["border"], "background": s["bg"]},
            "font": {"color": s["text"], "size": 12},
            "margin": 8,
            "widthConstraint": {"maximum": 140},
        })

    edges = []
    for ed in dag_data.get("edges", []):
        edges.append({
            "from": ed["source"],
            "to": ed["target"],
            "arrows": "to",
            "color": {"color": "#cbd5e1"},
        })

    return {"nodes": nodes, "edges": edges}


# ── NiceGUI 页面 ─────────────────────────────────────────

@ui.page('/')
def main_page():
    # ── 样式 ──
    ui.add_head_html('''
    <style>
        body { background: #f8fafc; }
        .page-title { font-size: 1.8rem; font-weight: 700; color: #0f172a; margin-bottom: 0.2rem; }
        .page-subtitle { font-size: 0.95rem; color: #64748b; margin-bottom: 1.5rem; }
        .section-title { font-size: 1.15rem; font-weight: 600; color: #1e293b; margin: 1.5rem 0 0.8rem; }
        .dag-container { border: 1px solid #e2e8f0; border-radius: 8px; background: white; }
        .detail-card { background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.2rem; margin-top: 0.8rem; }
        .agent-chip { display: inline-flex; align-items: center; gap: 4px; padding: 4px 12px;
                       border-radius: 100px; font-size: 0.8rem; font-weight: 500; margin: 2px; }
        .status-running { background: #dbeafe; color: #1d4ed8; }
        .status-completed { background: #dcfce7; color: #15803d; }
        .status-failed { background: #fee2e2; color: #dc2626; }
        .status-pending { background: #f1f5f9; color: #64748b; }
        .report-card { background: white; border: 2px solid #3b82f6; border-radius: 12px; padding: 1.5rem; }
        .scenario-btn { width: 100%; text-align: left; }
    </style>
    ''')

    # vis.js CDN
    ui.add_head_html('<script src="https://unpkg.com/vis-network@9.1.9/standalone/umd/vis-network.min.js"></script>')

    # ── 引用 ──
    dag_container = ui.element('div')
    detail_card = ui.element('div')
    report_section = ui.element('div')
    log_section = ui.element('div')
    status_label = ui.label('').classes('text-sm text-gray-500')

    # 隐藏元素用于 JS→Python 通信
    clicked_node = ui.input(value='').classes('hidden').props('id=clicked-node-input')

    # 定时器：检测节点点击
    def check_node_click():
        val = clicked_node.value
        if val and state.dag_data:
            show_node_detail(val)
            clicked_node.set_value('')

    ui.timer(0.5, check_node_click)

    # ── DAG 渲染函数 ──
    def render_dag():
        """渲染或更新 DAG"""
        if not state.dag_data:
            return
        data = build_vis_data(state.dag_data)
        dag_container.clear()
        with dag_container:
            ui.html(f'''
            <div id="dag-network" style="height: 320px; border: 1px solid #e2e8f0; border-radius: 8px; background: white;"></div>
            <script>
                (function() {{
                    var container = document.getElementById('dag-network');
                    window._dag_nodes = new vis.DataSet({data['nodes']});
                    window._dag_edges = new vis.DataSet({data['edges']});
                    window._dag_network = new vis.Network(container, {{
                        nodes: window._dag_nodes,
                        edges: window._dag_edges,
                    }}, {{
                        layout: {{
                            hierarchical: {{
                                enabled: true,
                                direction: 'UD',
                                sortMethod: 'directed',
                                levelSeparation: 80,
                                nodeSpacing: 140,
                            }}
                        }},
                        physics: false,
                        interaction: {{hover: true, tooltipDelay: 100}},
                    }});
                    window._dag_network.on('click', function(params) {{
                        if (params.nodes.length > 0) {{
                            var nodeId = params.nodes[0];
                            // 写入隐藏 input，触发 Python 检测
                            var input = document.getElementById('clicked-node-input');
                            if (input) {{
                                // 触发 NiceGUI 的 input 事件
                                var nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                                nativeInputValueSetter.call(input, nodeId);
                                input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            }}
                        }}
                    }});
                }})();
            </script>
            ''')

    # ── 节点详情 ──
    def show_node_detail(node_id: str):
        detail_card.clear()
        if not state.dag_data:
            return

        node_info = None
        for nd in state.dag_data.get("nodes", []):
            if nd["id"] == node_id:
                node_info = nd
                break
        if not node_info:
            return

        meta = get_meta(node_info.get("agent_type", ""))
        status = state.node_status.get(node_id, "pending")
        status_text = {"pending": "⏳ 等待中", "running": "🔄 执行中", "completed": "✅ 完成", "failed": "❌ 失败"}

        with detail_card:
            with ui.card().classes('w-full'):
                ui.label(f'{meta["icon"]} {meta["label"]} · {status_text.get(status, status)}').classes('text-base font-semibold')
                ui.label(node_info.get("task", "")).classes('text-sm text-gray-500')

                if node_id in state.results:
                    result = state.results[node_id]
                    if result.success and result.output:
                        if isinstance(result.output, dict):
                            text = result.output.get("raw_analysis") or result.output.get("raw_report")
                            if text:
                                ui.markdown(text)
                            else:
                                ui.code(str(result.output), language='json')
                        else:
                            ui.markdown(str(result.output))
                    elif not result.success:
                        ui.label(f'❌ {result.error}').classes('text-red-500')
                elif status == "running":
                    ui.label("正在执行中…").classes('text-blue-500')
                else:
                    ui.label("等待前置任务完成").classes('text-gray-400')

    # ── 最终报告 ──
    def show_report():
        report_section.clear()
        for nid, result in state.results.items():
            if "reflection" in nid.lower() and result.success:
                with report_section:
                    ui.label('📋 最终决策报告').classes('section-title')
                    with ui.card().classes('report-card w-full'):
                        if isinstance(result.output, dict) and "raw_report" in result.output:
                            ui.markdown(result.output["raw_report"])
                        else:
                            ui.markdown(str(result.output))
                break

    # ── Agent 结果概览 ──
    def show_agent_chips():
        if not state.dag_data or not state.results:
            return
        analysis = {k: v for k, v in state.results.items() if "reflection" not in k.lower()}
        if not analysis:
            return

        with log_section:
            ui.label('📝 Agent 分析结果').classes('section-title')
            with ui.row().classes('gap-2'):
                for nid, result in analysis.items():
                    meta = get_meta(result.agent_name.lower().replace(" agent", "").replace(" ", "_"))
                    status_cls = "status-completed" if result.success else "status-failed"
                    icon = "✅" if result.success else "❌"
                    ui.html(f'<span class="agent-chip {status_cls}">{icon} {meta["icon"]} {meta["label"]}</span>')

    # ── 执行流程 ──
    async def run_execution(task: str):
        state.reset()
        detail_card.clear()
        report_section.clear()
        log_section.clear()
        status_label.set_text('🎯 Planner Agent 正在分析任务…')

        # Planner
        result = await PlannerAgent().execute(task)
        if not result.success:
            status_label.set_text(f'❌ 任务规划失败: {result.error}')
            return

        state.dag_data = result.output
        for nd in result.output.get("nodes", []):
            state.node_status[nd["id"]] = "pending"
        status_label.set_text('✅ 任务规划完成，正在执行各 Agent…')
        render_dag()

        # 执行 DAG
        agents = {
            "weather": WeatherAgent(),
            "traffic": TrafficAgent(),
            "resource": ResourceAgent(),
            "reflection": ReflectionAgent(),
        }
        dag = DAG.from_dict(state.dag_data)
        executor = DAGExecutor(agents)

        def on_start(node):
            state.node_status[node.id] = "running"
            # 实时更新 DAG 节点颜色
            ui.run_javascript(f'''
                if (window._dag_nodes) {{
                    window._dag_nodes.update({{
                        id: "{node.id}",
                        color: {{border: "#3b82f6", background: "#dbeafe"}},
                        font: {{color: "#1d4ed8"}}
                    }});
                }}
            ''')

        def on_complete(node, r):
            state.results[node.id] = r
            state.node_status[node.id] = "completed" if r.success else "failed"
            # 实时更新节点颜色
            color = {"border": "#22c55e", "bg": "#dcfce7", "text": "#15803d"} if r.success else {"border": "#ef4444", "bg": "#fee2e2", "text": "#dc2626"}
            ui.run_javascript(f'''
                if (window._dag_nodes) {{
                    window._dag_nodes.update({{
                        id: "{node.id}",
                        color: {{border: "{color['border']}", background: "{color['bg']}"}},
                        font: {{color: "{color['text']}"}}
                    }});
                }}
            ''')

        executor.on_node_start(on_start)
        executor.on_node_complete(on_complete)

        results = await executor.execute(dag)
        state.results = results

        done = sum(1 for r in results.values() if r.success)
        status_label.set_text(f'✅ 执行完成 ({done}/{len(results)} 成功)')

        # 最终更新
        render_dag()
        show_agent_chips()
        show_report()

        # 默认选中 reflection
        for nd in state.dag_data.get("nodes", []):
            if nd.get("agent_type") == "reflection":
                show_node_detail(nd["id"])
                break

    # ── 布局 ──

    # 侧边栏
    with ui.left_drawer().classes('bg-gray-900 text-white'):
        ui.label('📋 系统说明').classes('text-lg font-bold text-white')
        ui.markdown('''
        **核心特点**
        - 动态规划：Planner 自动生成任务流程
        - 异构协同：多个专业 Agent 协同工作
        - DAG 工作流：支持并行执行

        **使用方法**
        1. 输入任务描述
        2. 点击"开始执行"
        3. 点击 DAG 中的节点查看详情
        ''').classes('text-gray-300 text-sm')

        ui.separator().classes('bg-gray-700')
        ui.label('🎯 预设场景').classes('text-sm font-semibold text-gray-400 mt-2')

        scenarios = {
            "🌧️ 暴雨应急": "某城市气象台发布暴雨红色预警，预计未来6小时降雨量将超过100毫米。请制定应急响应方案。",
            "🏟️ 大型活动": "某城市将举办大型体育赛事，预计观众超过10万人。请制定赛事保障方案。",
            "🏥 疫情防控": "某地区出现突发公共卫生事件，需要制定应急响应方案。",
        }
        task_input_ref = {'el': None}

        for name, task in scenarios.items():
            ui.button(name, on_click=lambda t=task: (task_input_ref['el'].set_value(t), )).classes('scenario-btn').props('flat text-color=gray-300')

    # 主内容
    with ui.column().classes('w-full max-w-4xl mx-auto p-6'):
        ui.label('动态规划式异构多智能体系统').classes('page-title')
        ui.label('基于 Planner Agent 与 DAG Workflow 的城市智能决策应用').classes('page-subtitle')

        # 输入区
        task_input = ui.textarea(
            placeholder='例如：某城市突发暴雨，请制定应急响应方案。',
        ).classes('w-full').props('outlined rows=2')
        task_input_ref['el'] = task_input

        ui.button('🚀 开始执行', on_click=lambda: run_execution(task_input.value)).props('color=primary unelevated').classes('mt-2')

        status_label

        # DAG 区
        dag_container
        detail_card

        # 结果区
        log_section
        report_section


# ── 启动 ──────────────────────────────────────────────────
if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title='动态规划式异构多智能体系统',
        favicon='🤖',
        port=8080,
        reload=False,
    )
