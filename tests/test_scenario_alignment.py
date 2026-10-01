"""
Scenario alignment tests.

These tests keep the code/demo data synchronized with the revised presentation:
the main case is the Nanshan rainstorm emergency decision scenario.
"""

import json
from pathlib import Path

from src.demo.web_demo import DEFAULT_TASK, DEMO_DAG, STATIC_RESULTS
from src.environment.simulator import EnvironmentSimulator


def test_emergency_scenario_matches_revised_presentation():
    data = json.loads(Path("demo/scenarios/emergency.json").read_text(encoding="utf-8"))

    assert data["name"] == "南山区暴雨应急智能决策"
    assert "深圳南山区" in data["task"]
    assert "80mm" in data["task"]
    assert "8.5/10" in data["task"]
    assert "5km" in data["task"]
    assert "临时封闭A路段低洼入口" in data["expected_decision"][0]


def test_environment_simulator_defaults_to_nanshan_case():
    simulator = EnvironmentSimulator(seed=1)

    weather = simulator.simulate_weather()
    traffic = simulator.simulate_traffic()
    resources = simulator.simulate_resources()

    assert weather["area"] == "深圳市南山区科技园周边"
    assert weather["rainfall_mm"] == 80
    assert traffic["congestion_index"] == 8.5
    assert traffic["alternate_road"] == "B绕行道路"
    assert resources["emergency_centers"]["nearest_distance_km"] == 5


def test_demo_static_data_contains_required_agents_and_decisions():
    agent_types = {node["agent_type"] for node in DEMO_DAG["nodes"]}

    assert {"planner", "weather", "traffic", "resource", "reflection"} <= agent_types
    assert "深圳南山区" in DEFAULT_TASK

    report = STATIC_RESULTS["reflection_1"].output["raw_report"]
    assert "临时封闭A路段低洼入口" in report
    assert "调度最近救援中心车辆和排水设备" in report
    assert "发布区域预警" in report
    assert "绕行B路段" in report
