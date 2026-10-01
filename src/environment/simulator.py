"""
EnvironmentSimulator - 环境模拟器
模拟城市环境数据，用于演示和测试
"""

import random
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


class EnvironmentSimulator:
    """
    环境模拟器

    生成模拟的城市环境数据，包括天气、交通、资源等。
    用于在没有真实数据源时进行演示。
    """

    def __init__(self, seed: Optional[int] = None):
        """
        初始化模拟器

        Args:
            seed: 随机种子，用于结果可复现
        """
        if seed is not None:
            random.seed(seed)

    def simulate_weather(self, scenario: str = "暴雨") -> Dict[str, Any]:
        """
        模拟天气数据

        Args:
            scenario: 场景类型（暴雨/高温/寒潮等）

        Returns:
            Dict: 天气数据
        """
        weather_data = {
            "暴雨": {
                "condition": "暴雨",
                "rainfall_mm": random.randint(80, 200),
                "wind_speed_kmh": random.randint(30, 60),
                "visibility_km": random.uniform(0.5, 3.0),
                "temperature_c": random.randint(18, 25),
                "humidity_percent": random.randint(85, 98),
                "risk_level": "极高",
                "warning": "暴雨红色预警",
            },
            "高温": {
                "condition": "高温",
                "temperature_c": random.randint(38, 42),
                "humidity_percent": random.randint(60, 80),
                "heat_index": random.randint(42, 50),
                "risk_level": "高",
                "warning": "高温橙色预警",
            },
            "寒潮": {
                "condition": "寒潮",
                "temperature_c": random.randint(-15, -5),
                "wind_speed_kmh": random.randint(40, 70),
                "wind_chill": random.randint(-25, -15),
                "risk_level": "高",
                "warning": "寒潮蓝色预警",
            },
        }

        return weather_data.get(scenario, weather_data["暴雨"])

    def simulate_traffic(self, weather_condition: str = "暴雨") -> Dict[str, Any]:
        """
        模拟交通数据

        Args:
            weather_condition: 天气状况

        Returns:
            Dict: 交通数据
        """
        # 根据天气调整交通状况
        congestion_multiplier = {
            "暴雨": 1.8,
            "高温": 1.2,
            "寒潮": 1.5,
        }.get(weather_condition, 1.0)

        base_congestion = random.randint(30, 60)
        congestion_level = min(100, int(base_congestion * congestion_multiplier))

        return {
            "congestion_level": congestion_level,
            "congestion_description": self._get_congestion_description(congestion_level),
            "affected_roads": self._generate_affected_roads(congestion_level),
            "accident_count": random.randint(0, 5) if congestion_level > 60 else random.randint(0, 2),
            "public_transport_status": "部分停运" if congestion_level > 70 else "正常运营",
            "emergency_lanes_clear": congestion_level < 80,
        }

    def simulate_resources(self, emergency_level: str = "高") -> Dict[str, Any]:
        """
        模拟资源数据

        Args:
            emergency_level: 应急等级

        Returns:
            Dict: 资源数据
        """
        resource_multiplier = {
            "极高": 2.0,
            "高": 1.5,
            "中": 1.0,
            "低": 0.5,
        }.get(emergency_level, 1.0)

        return {
            "emergency_teams": {
                "available": int(random.randint(10, 30) / resource_multiplier),
                "total": 50,
                "deployed": int(random.randint(5, 20) * resource_multiplier),
            },
            "rescue_equipment": {
                "boats": {"available": random.randint(5, 15), "total": 30},
                "pumps": {"available": random.randint(10, 25), "total": 50},
                "generators": {"available": random.randint(8, 20), "total": 40},
            },
            "shelters": {
                "capacity": random.randint(5000, 20000),
                "current_occupancy": random.randint(1000, 8000),
                "locations": random.randint(5, 15),
            },
            "medical_resources": {
                "hospitals_on_alert": random.randint(3, 10),
                "ambulances_available": random.randint(10, 30),
                "medical_teams": random.randint(5, 15),
            },
        }

    def _get_congestion_description(self, level: int) -> str:
        """获取拥堵描述"""
        if level >= 80:
            return "严重拥堵"
        elif level >= 60:
            return "中度拥堵"
        elif level >= 40:
            return "轻度拥堵"
        else:
            return "基本畅通"

    def _generate_affected_roads(self, congestion_level: int) -> list:
        """生成受影响路段"""
        roads = [
            "二环路东段", "三环路北段", "长安街", "建国门外大街",
            "西直门外大街", "东四环", "北四环", "南三环",
        ]
        count = min(len(roads), congestion_level // 15)
        return random.sample(roads, count)
