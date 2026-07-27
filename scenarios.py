"""
Модуль сценариев
"""

from typing import Dict, Optional, List
from dataclasses import dataclass


@dataclass
class ScenarioConfig:
    name: str
    description: str
    modifiers: Dict[str, float]


SCENARIOS = {
    "base": ScenarioConfig(
        name="base",
        description="Базовый сценарий",
        modifiers={}
    ),
    "optimistic": ScenarioConfig(
        name="optimistic",
        description="Оптимистичный сценарий",
        modifiers={
            "customers_growth_monthly": 5.0,
            "cost_per_client_monthly": 0.9,
            "discount_rate": -3.0
        }
    ),
    "pessimistic": ScenarioConfig(
        name="pessimistic",
        description="Пессимистичный сценарий",
        modifiers={
            "customers_growth_monthly": -5.0,
            "cost_per_client_monthly": 1.2,
            "monthly_customers_start": 0.7,
            "discount_rate": 5.0
        }
    )
}


def get_scenario_modifiers(name: str) -> Dict[str, float]:
    if name not in SCENARIOS:
        return {}
    return SCENARIOS[name].modifiers.copy()


def get_all_scenarios() -> List[str]:
    return list(SCENARIOS.keys())